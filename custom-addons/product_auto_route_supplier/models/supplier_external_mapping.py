# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SupplierExternalMapping(models.Model):
    _name = 'supplier.external.mapping'
    _description = 'External Code to Vendor Conversion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority, external_supplier_comp_code'

    # Fields
    external_supplier_comp_code = fields.Char(
        string='External Company Code',
        required=True,
        size=20,
        index=True,
        tracking=True,
        help='Supplier company code from external system (API)'
    )
    
    external_supplier_name = fields.Char(
        string='External Company Name',
        size=100,
        tracking=True,
        help='Supplier name from external system (supplementary information)'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor (Odoo)',
        required=True,
        domain="[('is_company', '=', True), ('supplier_rank', '>', 0)]",
        tracking=True,
        ondelete='restrict',
        help='Vendor record in Odoo. Must be a company with supplier rank > 0'
    )
    
    priority = fields.Integer(
        string='Priority',
        default=10,
        tracking=True,
        help='Lower number = higher priority when multiple matches exist'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Only active records are used in conversion logic'
    )
    
    note = fields.Text(
        string='Notes',
        help='Record operational notes or precautions'
    )
    
    # Computed field for display
    display_name_full = fields.Char(
        string='Full Display Name',
        compute='_compute_display_name_full',
        store=True
    )

    _sql_constraints = [
        ('unique_external_code_active',
         'UNIQUE(external_supplier_comp_code, active) WHERE active = true',
         'Only one active record per external supplier code is allowed!'),
        ('priority_positive',
         'CHECK(priority >= 0)',
         'Priority must be a positive number!')
    ]

    @api.depends('external_supplier_comp_code', 'external_supplier_name', 'partner_id')
    def _compute_display_name_full(self):
        """Compute full display name"""
        for record in self:
            name = f"{record.external_supplier_comp_code}"
            if record.external_supplier_name:
                name += f" - {record.external_supplier_name}"
            if record.partner_id:
                name += f" → {record.partner_id.name}"
            record.display_name_full = name

    @api.constrains('external_supplier_comp_code')
    def _check_external_code(self):
        """Validate external supplier code"""
        for record in self:
            if not record.external_supplier_comp_code:
                raise ValidationError(_('External Company Code is required!'))
            
            # Trim whitespace
            code = record.external_supplier_comp_code.strip()
            if not code:
                raise ValidationError(_('External Company Code cannot be empty or whitespace only!'))
            
            # Update with trimmed value if different
            if code != record.external_supplier_comp_code:
                record.external_supplier_comp_code = code

    @api.constrains('partner_id', 'active')
    def _check_partner_vendor(self):
        """Ensure partner is a valid vendor"""
        for record in self:
            if record.active and record.partner_id:
                if not record.partner_id.is_company:
                    raise ValidationError(_(
                        'Partner %s must be a company!' % record.partner_id.name
                    ))
                if record.partner_id.supplier_rank <= 0:
                    raise ValidationError(_(
                        'Partner %s must have supplier rank > 0!' % record.partner_id.name
                    ))

    def name_get(self):
        """Display name format"""
        result = []
        for record in self:
            name = f"{record.external_supplier_comp_code}"
            if record.external_supplier_name:
                name += f" - {record.external_supplier_name}"
            if record.partner_id:
                name += f" → {record.partner_id.name}"
            result.append((record.id, name))
        return result

    @api.model
    def get_vendor_from_external_code(self, external_supplier_comp_code):
        """
        Convert external supplier code to Odoo vendor
        
        Args:
            external_supplier_comp_code: External supplier company code
            
        Returns:
            res.partner record or False if not found
        """
        if not external_supplier_comp_code:
            _logger.debug("get_vendor_from_external_code: No code provided")
            return False
        
        # Trim whitespace
        code = external_supplier_comp_code.strip()
        
        mapping = self.search([
            ('external_supplier_comp_code', '=', code),
            ('active', '=', True)
        ], limit=1, order='priority, id')
        
        if mapping:
            _logger.info(
                f"Vendor mapping found: {code} → "
                f"{mapping.partner_id.name} (ID: {mapping.partner_id.id})"
            )
            return mapping.partner_id
        else:
            _logger.warning(
                f"Supplier mapping not found for code: {code}"
            )
            return False

    @api.model
    def get_all_vendor_codes(self):
        """
        Get all active external supplier codes
        
        Returns:
            list: List of (code, vendor_id) tuples
        """
        mappings = self.search([('active', '=', True)], order='priority, external_supplier_comp_code')
        return [(m.external_supplier_comp_code, m.partner_id.id) for m in mappings]
