# -*- coding: utf-8 -*-
import base64
import json
import time
import requests
from odoo import api, models, _
from odoo.exceptions import UserError

API_BASE = "https://api-staging.bio-purchase.com"
LOGIN_URL = f"{API_BASE}/api/ec-users/authenticate"
DATA_URL = f"{API_BASE}/v1/get_product_ec102"

# Default credentials (override in Settings ▸ Technical ▸ System Parameters)
#   ir.config_parameter keys:
#     ec250_api.username
#     ec250_api.password
#     ec250_api.login_url
#     ec250_api.data_url
DEFAULT_USERNAME = "bpm_customer_001"
DEFAULT_PASSWORD = "pM49LbkD"


class Ec250ApiMixin(models.AbstractModel):
    _name = "ec250.api.mixin"
    _description = "EC250 API helper mixin"

    # ---------- Config helpers ----------
    def _get_param(self, key, default=None):
        return self.env["ir.config_parameter"].sudo().get_param(key, default)

    def _set_param(self, key, value):
        self.env["ir.config_parameter"].sudo().set_param(key, value or "")

    # ---------- Token handling ----------
    def _decode_jwt_exp(self, token):
        """Decode JWT 'exp' (no verification). Returns int epoch or None."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            payload_b64 = parts[1]
            padding = "=" * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64 + padding)
            payload = json.loads(payload_json.decode("utf-8"))
            return int(payload.get("exp")) if payload.get("exp") else None
        except Exception:
            return None

    def _get_cached_token(self):
        token = self._get_param("ec250_api.token")
        exp = self._get_param("ec250_api.token_exp")
        if token and exp:
            try:
                exp = int(exp)
            except Exception:
                exp = None
        # Consider token expired if exp <= now - 60s (clock skew buffer)
        if token and exp and (time.time() < exp - 60):
            return token
        return None

    def _login_and_cache_token(self):
        username = self._get_param("ec250_api.username", DEFAULT_USERNAME)
        password = self._get_param("ec250_api.password", DEFAULT_PASSWORD)
        login_url = self._get_param("ec250_api.login_url", LOGIN_URL)

        # ---- PRINT: login request ----
        print(f"Login URL: {login_url}")
        print(f"Login payload: username={username}, password={'*' * len(password) if password else ''}")

        try:
            # ✅ Send credentials in form-data body (not query params)
            resp = requests.post(
                login_url,
                data={"username": username, "password": password},
                timeout=20,
            )
        except requests.RequestException as e:
            raise UserError(_("Login request failed: %s") % e)

        # ---- PRINT: raw login response ----
        try:
            raw_text = resp.text
        except Exception:
            raw_text = "<no text>"
        print(f"Login response status: {resp.status_code}")
        print(f"Login response raw: {raw_text}")

        if resp.status_code != 200:
            raise UserError(_("Login failed (HTTP %s): %s") % (resp.status_code, raw_text))

        try:
            data = resp.json()
        except ValueError:
            raise UserError(_("Login returned non-JSON response."))

        # ---- PRINT: parsed login response ----
        print(f"Login response JSON: {json.dumps(data, ensure_ascii=False)}")

        if data.get("http") != 200 or not data.get("token"):
            raise UserError(_("Login failed: %s") % data)

        token = data["token"]
        exp = self._decode_jwt_exp(token) or (int(time.time()) + 1800)  # fallback 30m

        self._set_param("ec250_api.token", token)
        self._set_param("ec250_api.token_exp", str(exp))

        # ---- PRINT: token summary ----
        print(f"Token cached. Expires at (epoch): {exp}")

        return token

    def _get_valid_token(self):
        token = self._get_cached_token()
        if token:
            print("Using cached token.")
            return token
        print("No valid cached token. Logging in...")
        return self._login_and_cache_token()

    # ---------- Data fetch ----------
    def _api_search_products(self, params):
        """
        params: dict keys:
          keywords, supplier_sku, name, maker_name, sales_origin_maker_name, cas_code, page, limit
        """
        data_url = self._get_param("ec250_api.data_url", DATA_URL)
        token = self._get_valid_token()

        q = {
            "token": token,
            "page": params.get("page") or 1,
            "limit": params.get("limit") or 20,
            "keywords": (params.get("keywords") or "").strip(),
            "supplier_sku": (params.get("supplier_sku") or "").strip(),
            "name": (params.get("name") or "").strip(),
            "maker_name": (params.get("maker_name") or "").strip(),
            "sales_origin_maker_name": (params.get("sales_origin_maker_name") or "").strip(),
            "cas_code": (params.get("cas_code") or "").strip(),
        }

        # ---- PRINT: data request ----
        print("Data URL:", data_url)
        print("Data query params:", q)

        try:
            resp = requests.get(data_url, params=q, timeout=30)
        except requests.RequestException as e:
            raise UserError(_("Data request failed: %s") % e)

        # If token is invalid/expired, re-login once and retry
        if resp.status_code in (401, 403):
            print(f"Data fetch got {resp.status_code}. Token may be invalid/expired. Re-logging in...")
            q["token"] = self._login_and_cache_token()
            try:
                resp = requests.get(data_url, params=q, timeout=30)
            except requests.RequestException as e:
                raise UserError(_("Data request failed (after relogin): %s") % e)

        # ---- PRINT: raw data response ----
        try:
            raw_text = resp.text
        except Exception:
            raw_text = "<no text>"
        print(f"Data response status: {resp.status_code}")
        print(f"Data response raw: {raw_text}")

        if resp.status_code != 200:
            raise UserError(_("Data fetch failed (HTTP %s): %s") % (resp.status_code, raw_text))

        try:
            data = resp.json()
        except ValueError:
            raise UserError(_("Data fetch returned non-JSON response."))

        # ---- PRINT: parsed data response ----
        print(f"Data response JSON: {json.dumps(data, ensure_ascii=False)[:5000]}")  # guard very long logs

        # Some backends return HTTP 200 but a non-200 JSON envelope
        if data.get("http") != 200:
            msg = (data.get("message") or "").lower()
            print(f"Data envelope http != 200. message={msg}")
            if "token" in msg:
                print("Retrying after token refresh due to token-related message...")
                q["token"] = self._login_and_cache_token()
                resp = requests.get(data_url, params=q, timeout=30)
                if resp.status_code != 200:
                    raise UserError(_("Data fetch failed after token refresh (HTTP %s): %s") % (resp.status_code, resp.text))
                data = resp.json()
                print(f"Data response JSON (after refresh): {json.dumps(data, ensure_ascii=False)[:5000]}")
            else:
                raise UserError(_("Data fetch failed: %s") % data)

        total = int(data.get("total") or 0)
        items = data.get("product_list") or []

        # ---- PRINT: short summary ----
        print(f"Data fetch OK. total={total}, items_returned={len(items)}")

        return {
            "total": total,
            "items": items,
        }
