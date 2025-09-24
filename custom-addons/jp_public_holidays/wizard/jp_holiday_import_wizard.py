import base64
import csv
import io
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError

# NEW: use requests for the API
try:
    import requests
except Exception:  # pragma: no cover
    requests = None


class JPHolidayImportWizard(models.TransientModel):
    _name = "jp.holiday.import.wizard"
    _description = "Import JP Holidays"
    
    def _default_year(self):
        return int(self.env.context.get("default_year") or date.today().year)
    year = fields.Integer(string="Year", required=True, default=_default_year)

    # year = fields.Integer(string="Year", required=True, default=lambda self: date.today().year)
    file = fields.Binary(string="CSV File", required=False)  # changed: not required
    filename = fields.Char()
    note = fields.Text(readonly=True, help="Import result summary.")

    def _upsert_holidays(self, pairs, year):
        """pairs: iterable of (date_str, name_str)"""
        created = updated = skipped = 0
        Holiday = self.env["jp.holiday"].sudo()

        for dt, nm in pairs:
            if not dt or not nm:
                skipped += 1
                continue
            if not dt.startswith(str(year)):
                skipped += 1
                continue

            existing = Holiday.search([("date", "=", dt)], limit=1)
            if existing:
                if existing.name != nm:
                    existing.name = nm
                    updated += 1
                else:
                    skipped += 1
                continue

            Holiday.create({"date": dt, "name": nm})
            created += 1

        return created, updated, skipped

    # Existing CSV import
    def action_import(self):
        """Expect CSV with headers: date,name  (date: YYYY-MM-DD)"""
        self.ensure_one()
        if not self.file:
            raise UserError("Please upload a CSV file before clicking Import.")

        try:
            csv_bytes = base64.b64decode(self.file)
            f = io.StringIO(csv_bytes.decode("utf-8"))
            reader = csv.DictReader(f)
        except Exception as e:
            raise UserError(f"Could not read CSV: {e}")

        pairs = ((row.get("date"), row.get("name")) for row in reader)
        created, updated, skipped = self._upsert_holidays(pairs, self.year)

        self.note = f"CSV Import for {self.year}\nCreated: {created}, Updated: {updated}, Skipped: {skipped}"
        return {
            "type": "ir.actions.act_window",
            "res_model": "jp.holiday.import.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    # NEW: Fetch from API
    def action_fetch_api(self):
        """
        Fetch holidays from:
          https://holidays-jp.github.io/api/v1/<YEAR>/date.json
        Response is a JSON object: { "YYYY-MM-DD": "Japanese Name", ... }
        """
        self.ensure_one()
        if requests is None:
            raise UserError("The Python package 'requests' is not installed. Please install it on the Odoo server.")

        url = f"https://holidays-jp.github.io/api/v1/{self.year}/date.json"
        try:
            resp = requests.get(
                url,
                timeout=12,
                headers={
                    "User-Agent": f"Odoo/18 jp_public_holidays (+https://github.com/holidays-jp/holidays-jp)"
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise UserError("Unexpected API response format (expected a JSON object).")
        except requests.exceptions.RequestException as e:
            raise UserError(f"API request failed: {e}")
        except ValueError as e:
            raise UserError(f"Invalid JSON from API: {e}")

        # Convert dict to iterable of (date, name)
        pairs = sorted(data.items())  # sort for consistent processing
        created, updated, skipped = self._upsert_holidays(pairs, self.year)

        self.note = f"API Fetch {url}\nCreated: {created}, Updated: {updated}, Skipped: {skipped}"
        return {
            "type": "ir.actions.act_window",
            "res_model": "jp.holiday.import.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }
