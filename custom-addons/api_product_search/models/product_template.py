from odoo import models, fields, api
import requests


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = args
        if name:
            domain = ['|', ('name', operator, name)] + args
        records = self.search(domain, limit=limit)
        results = records.name_get()

        # 🔹 Call external API if search term is provided
        if name:
            try:
                # Step 1: Authenticate (you might want to cache the token for performance)
                auth_url = "https://api-staging.bio-purchase.com/api/ec-users/authenticate"
                auth_payload = {
                    "username": "ORDIA-test01",
                    "password": "Zc2Mb3At"
                }
                auth_response = requests.post(auth_url, data=auth_payload, timeout=10)
                auth_data = auth_response.json()

                if auth_data.get("http") == 200:
                    token = auth_data["token"]

                    # Step 2: Call product API with search keyword
                    product_url = (
                        f"https://api-staging.bio-purchase.com/v1/get_product_ec102"
                        f"?token={token}&page=1&limit=20&keywords={name}&no_type=4"
                    )
                    product_response = requests.get(product_url, timeout=10)
                    product_data = product_response.json()

                    if product_data.get("http") == 200 and product_data.get("total", 0) > 0:
                        for p in product_data["product_list"]:
                            display_name = f"[{p['sku']}] {p['name_jp']} ({p['volume_unit_label']})"
                            # Use negative IDs to avoid conflict with real products
                            results.append((-p["id"], display_name))
            except Exception as e:
                # Log the error for debugging
                _logger = self.env['ir.logging']
                _logger.create({
                    'name': 'API Product Search',
                    'type': 'server',
                    'level': 'ERROR',
                    'dbname': self._cr.dbname,
                    'message': str(e),
                    'path': 'product.template',
                    'func': 'name_search',
                    'line': '0',
                })

        return results

    def name_get(self):
        result = []
        for product in self:
            name = product.name
            result.append((product.id, name))
        return result
