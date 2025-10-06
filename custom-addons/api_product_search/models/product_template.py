from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Extra API fields
    api_sku = fields.Char("API SKU")
    api_supplier_sku = fields.Char("API Supplier SKU")
    api_maker = fields.Char("API Maker")
    api_volume = fields.Char("API Volume/Unit")
    api_list_price = fields.Float("API List Price")

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Override search:
        1. Search in Odoo DB
        2. If not found, query external API
        3. Create products in DB if missing
        """
        args = args or []
        results = []

        # Step A: Normal Odoo products
        records = self.search([('name', operator, name)] + args, limit=limit)
        if records:
            results = records.name_get()

        # Step B: External API search
        if name:
            try:
                # API Authentication
                auth_url = "https://api-staging.bio-purchase.com/api/ec-users/authenticate"
                auth_payload = {"username": "ORDIA-test01", "password": "Zc2Mb3At"}
                auth_response = requests.post(auth_url, data=auth_payload, timeout=10)
                auth_data = auth_response.json()
                if auth_data.get("http") != 200:
                    return results
                token = auth_data["token"]

                # Search products from API
                product_url = (
                    f"https://api-staging.bio-purchase.com/v1/get_product_ec102"
                    f"?token={token}&page=1&limit=20&keywords={name}&no_type=4"
                )
                product_response = requests.get(product_url, timeout=10)
                product_data = product_response.json()

                # Create product in Odoo if not already present
                if product_data.get("http") == 200 and product_data.get("total", 0) > 0:
                    for p in product_data["product_list"]:
                        product = self.search([('api_sku', '=', p['sku'])], limit=1)
                        if not product:
                            product = self.create({
                                "name": p['name_jp'],
                                "list_price": p.get("list_price", 0.0),  # Odoo native list_price
                                "api_sku": p["sku"],
                                "api_supplier_sku": p.get("supplier_sku"),
                                "api_maker": p.get("maker_name") or "Unknown",  # fallback if missing
                                "api_volume": p.get("volume_unit_label"),
                                "api_list_price": p.get("list_price", 0.0),
                            })

                        # Add to results dropdown
                        results.append((product.id,
                                        f"[{p['sku']}] {p['name_jp']} ({p.get('volume_unit_label', '')})"))

            except Exception as e:
                _logger.error("API Product Search failed: %s", e)

        return results

    def name_get(self):
        """
        Custom product display in dropdown:
        [SKU] Name (Volume) - Maker - Price
        """
        result = []
        for product in self:
            parts = []
            if product.api_sku:
                parts.append(f"[{product.api_sku}]")
            if product.name:
                parts.append(product.name)
            if product.api_volume:
                parts.append(f"({product.api_volume})")
            if product.api_maker:
                parts.append(f"- {product.api_maker}")

            # Always show a price (prefer API, fallback to Odoo list_price)
            price = product.api_list_price or product.list_price
            if price:
                parts.append(f"- {price:.2f}")

            display_name = " ".join(parts)
            result.append((product.id, display_name))
        return result
