# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Ec250ApiSearchWizard(models.TransientModel):
    _name = "ec250.api.search.wizard"
    _description = "EC250 API Search Wizard"
    _inherit = "ec250.api.mixin"

    # Link to sale order line
    sale_order_line_id = fields.Many2one(
        "sale.order.line", 
        string="Sale Order Line",
        readonly=True
    )

    # Search params
    keywords = fields.Char(string="Keywords")
    supplier_sku = fields.Char(string="Supplier SKU")
    name = fields.Char(string="Product Name")
    maker_name = fields.Char(string="Maker Name")
    sales_origin_maker_name = fields.Char(string="Sales Origin Maker Name")
    cas_code = fields.Char(string="CAS Code")

    page = fields.Integer(string="Page", default=1)
    limit = fields.Integer(string="Results per Page", default=20)

    # Results
    total = fields.Integer(string="Total Results", readonly=True, default=0)
    result_ids = fields.One2many(
        "ec250.api.search.result", 
        "wizard_id",
        string="Search Results"
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'sale.order.line':
            res['sale_order_line_id'] = self._context.get('active_id')
        return res

    def action_search(self):
        """Perform the API search"""
        self.ensure_one()
        
        # Validate inputs
        if self.limit <= 0:
            self.limit = 20
        if self.page <= 0:
            self.page = 1

        payload = {
            "keywords": self.keywords or "",
            "supplier_sku": self.supplier_sku or "",
            "name": self.name or "",
            "maker_name": self.maker_name or "",
            "sales_origin_maker_name": self.sales_origin_maker_name or "",
            "cas_code": self.cas_code or "",
            "page": self.page,
            "limit": self.limit,
        }

        # Call the API
        data = self._api_search_products(payload)
        items = data.get("items", [])
        
        # Clear previous results
        self.result_ids.unlink()
        
        # Create new result records
        results = []
        for item in items:
            results.append({
                "wizard_id": self.id,
                "ext_id": str(item.get("id", "")),
                "sku": item.get("sku", ""),
                "supplier_sku": item.get("supplier_sku", ""),
                "supplier_comp_code": item.get("supplier_comp_code", ""),
                "supplier_maker_code": item.get("supplier_maker_code", ""),
                "sales_origin_maker_name": item.get("sales_origin_maker_name", ""),
                "maker_name": item.get("maker_name", ""),
                "name_jp": item.get("name_jp", ""),
                "name": item.get("name", ""),
                "volume_unit_label": item.get("volume_unit_label", ""),
                "list_price": float(item.get("list_price", 0.0)),
            })
        
        if results:
            self.env["ec250.api.search.result"].create(results)
        
        # Update total count
        self.total = int(data.get("total", 0))
        
        # Return the same wizard view to show results
        return {
            "type": "ir.actions.act_window",
            "name": _("EC250 Product Search"),
            "res_model": "ec250.api.search.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": self._context,
        }