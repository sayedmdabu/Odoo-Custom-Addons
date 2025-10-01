from odoo import models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_external_product_search(self):
        """Open EC250 Search Wizard from Sale Order header"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("EC250 Product Search"),
            "res_model": "ec250.api.search.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "sale.order",
                "active_id": self.id,
            },
        }
