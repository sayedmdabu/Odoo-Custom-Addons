# -*- coding: utf-8 -*-
from odoo import api, fields, models

class Ec250ApiSearchResult(models.TransientModel):
    _name = "ec250.api.search.result"
    _description = "EC250 API Search Result (transient)"

    wizard_id = fields.Many2one("ec250.api.search.wizard", ondelete="cascade")

    ext_id = fields.Char(string="External ID")
    sku = fields.Char(string="SKU")
    supplier_sku = fields.Char(string="Supplier SKU")
    supplier_comp_code = fields.Char(string="Supplier Company Code")
    supplier_maker_code = fields.Char(string="Supplier Maker Code")
    sales_origin_maker_name = fields.Char(string="Sales Origin Maker")
    maker_name = fields.Char(string="Maker")
    name_jp = fields.Char(string="Name (JP)")
    name = fields.Char(string="Name")
    volume_unit_label = fields.Char(string="Volume/Unit")
    list_price = fields.Float(string="List Price")
