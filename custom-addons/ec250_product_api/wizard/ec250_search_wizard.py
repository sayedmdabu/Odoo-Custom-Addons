# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Ec250ApiSearchWizard(models.TransientModel):
    _name = "ec250.api.search.wizard"
    _description = "EC250 API Search Wizard"
    _inherit = "ec250.api.mixin"

    # Search params
    keywords = fields.Char()
    supplier_sku = fields.Char()
    name = fields.Char()
    maker_name = fields.Char()
    sales_origin_maker_name = fields.Char(string="Sales Origin Maker Name")
    cas_code = fields.Char()

    page = fields.Integer(default=1)
    limit = fields.Integer(default=20)

    # Results
    total = fields.Integer(readonly=True)
    result_ids = fields.One2many(
        "ec250.api.search.result", "wizard_id",
        string="Results", readonly=True
    )

    def action_search(self):
        self.ensure_one()
        if self.limit <= 0:
            self.limit = 20
        if self.page <= 0:
            self.page = 1

        payload = {
            "keywords": self.keywords,
            "supplier_sku": self.supplier_sku,
            "name": self.name,
            "maker_name": self.maker_name,
            "sales_origin_maker_name": self.sales_origin_maker_name,
            "cas_code": self.cas_code,
            "page": self.page,
            "limit": self.limit,
        }

        # This call will: (1) login to get token in background if needed,
        # (2) fetch products, (3) auto-refresh token if expired.
        data = self._api_search_products(payload)
        items = data["items"]

        # Reset previous results
        self.result_ids.unlink()

        # Insert fresh rows
        lines = []
        for it in items:
            lines.append({
                "wizard_id": self.id,
                "ext_id": str(it.get("id") or ""),
                "sku": it.get("sku") or "",
                "supplier_sku": it.get("supplier_sku") or "",
                "supplier_comp_code": it.get("supplier_comp_code") or "",
                "supplier_maker_code": it.get("supplier_maker_code") or "",
                "sales_origin_maker_name": it.get("sales_origin_maker_name") or "",
                "maker_name": it.get("maker_name") or "",
                "name_jp": it.get("name_jp") or "",
                "name": it.get("name") or "",
                "volume_unit_label": it.get("volume_unit_label") or "",
                "list_price": it.get("list_price") or 0.0,
            })

        if lines:
            self.env["ec250.api.search.result"].create(lines)

        self.total = int(data.get("total") or 0)

        # Re-open wizard to display results
        return {
            "type": "ir.actions.act_window",
            "name": _("EC250 Product Search"),
            "res_model": "ec250.api.search.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }
