# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SupplierExternalMapping(models.Model):
    _name = 'supplier.external.mapping'
    _description = 'External Code to Vendor Conversion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'external_supplier_comp_code'

    external_supplier_comp_code = fields.Char(
        string='External Company Code',
        required=True,
        index=True,
        tracking=True
    )
    
    external_supplier_name = fields.Char(
        string='External Company Name',
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor (Odoo)',
        required=True,
        tracking=True,
        ondelete='restrict'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    note = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_external_code_active',
         'UNIQUE(external_supplier_comp_code, active) WHERE active = true',
         'Only one active record per external supplier code is allowed!')
    ]

    def name_get(self):
        result = []
        for record in self:
            name = record.external_supplier_comp_code
            if record.partner_id:
                name += f" → {record.partner_id.name}"
            result.append((record.id, name))
        return result

    @api.model
    def get_vendor_from_external_code(self, api_supplier_comp_code):
        if not api_supplier_comp_code:
            return False
        
        code = api_supplier_comp_code.strip()
        mapping = self.search([
            ('external_supplier_comp_code', '=', code),
            ('active', '=', True)
        ], limit=1)
        
        if mapping:
            return mapping.partner_id
        return False