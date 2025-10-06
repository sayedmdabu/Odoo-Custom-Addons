# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    # Stored columns that you want to see in the SO line grid
    sku = fields.Char("SKU", readonly=True, store=True)
    supplier_sku = fields.Char("Supplier SKU", readonly=True, store=True)
    maker = fields.Char("Maker", readonly=True, store=True)
    volume = fields.Char("Volume/Unit", readonly=True, store=True)
    list_price = fields.Float("List Price", readonly=True, store=True)

    # ----------------------------
    # Helpers
    # ----------------------------
    def _get_api_values_from_product(self, product):
        """
        Read once from product/template and return a dict that can be merged
        into create()/write() vals. This function MUST NOT write to 'self'.
        """
        if not product:
            return {
                "sku": False,
                "supplier_sku": False,
                "maker": False,
                "volume": False,
                "list_price": 0.0,
            }
        tmpl = product.product_tmpl_id
        return {
            "sku": tmpl.api_sku,
            "supplier_sku": tmpl.api_supplier_sku,
            "maker": tmpl.api_maker,
            "volume": tmpl.api_volume,
            # prefer API list price; fall back to template list_price if empty
            "list_price": tmpl.api_list_price or tmpl.list_price or 0.0,
        }

    # ----------------------------
    # Onchange: fills values in the form while editing
    # ----------------------------
    @api.onchange("product_id")
    def _onchange_product_id_fill(self):
        """Safe in-memory assignment (not persisted until save)."""
        for line in self:
            vals = line._get_api_values_from_product(line.product_id)
            line.update(vals)  # update() doesn't call write() in onchange context
            # Optional: override unit price in the UI if you want to see it immediately
            if line.product_id and line.product_id.product_tmpl_id.api_list_price:
                line.price_unit = line.product_id.product_tmpl_id.api_list_price

    # ----------------------------
    # Persist on create
    # ----------------------------
    @api.model
    def create(self, vals):
        vals = dict(vals)  # make a copy; we’ll enrich it
        # If product_id is present at creation, compute the api fields now
        product = None
        product_id = vals.get("product_id")
        if product_id:
            product = self.env["product.product"].browse(product_id)
            vals.update(self._get_api_values_from_product(product))
            # Optionally set the unit price from API list price
            api_lp = product.product_tmpl_id.api_list_price
            if api_lp:
                vals.setdefault("price_unit", api_lp)

        # Now create once with all values (no recursive writes)
        line = super().create(vals)
        return line

    # ----------------------------
    # Persist on write
    # ----------------------------
    def write(self, vals):
        """
        Never assign self.field = ... here.
        Compute and pass values to super().write() only.
        """
        # If product_id changes, we need to compute the new API values per line
        if "product_id" in vals:
            # Write per-record so each can compute from its own product
            # (avoids re-entering our write() through field assignment)
            for line in self:
                new_vals = dict(vals)
                new_product = self.env["product.product"].browse(new_vals["product_id"]) \
                    if new_vals.get("product_id") else line.product_id
                new_vals.update(line._get_api_values_from_product(new_product))

                api_lp = new_product.product_tmpl_id.api_list_price if new_product else False
                if api_lp:
                    # If you want price to follow API list price when product changes
                    new_vals.setdefault("price_unit", api_lp)

                super(SaleOrderLine, line).write(new_vals)
            return True

        # Product didn’t change; just write the incoming values
        return super().write(vals)
