# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class MakerRate(models.Model):
    _name = 'maker.rate'
    _description = 'Manufacturer Discount Rate'
    _order = 'supplier_comp_code, maker_name'
    _rec_name = 'display_name_full'

    # Fields
    supplier_comp_code = fields.Char(
        string='Supplier Code',
        required=True,
        size=20,
        index=True,
        help='External Supplier Code'
    )
    
    # Dropdown helper for supplier code selection
    supplier_comp_code_selection = fields.Selection(
        selection='_get_supplier_codes',
        string='Select Supplier Code',
        help='Select from existing supplier mappings (optional helper field)'
    )
    
    maker_name = fields.Char(
        string='Manufacturer Name',
        required=True,
        size=50,
        index=True,
        help='Manufacturer/Maker name'
    )
    
    # Dropdown helper for common manufacturers
    maker_name_selection = fields.Selection([
        ('Thermo Fisher', 'Thermo Fisher'),
        ('Sigma-Aldrich', 'Sigma-Aldrich'),
        ('Merck', 'Merck'),
        ('VWR', 'VWR'),
        ('Bio-Rad', 'Bio-Rad'),
        ('Agilent', 'Agilent'),
        ('Waters', 'Waters'),
        ('Shimadzu', 'Shimadzu'),
        ('PerkinElmer', 'PerkinElmer'),
        ('Sartorius', 'Sartorius'),
    ], string='Select Manufacturer', help='Select from common manufacturers (optional helper field)')
    
    # Quick discount percentage selector
    discount_percent_selection = fields.Selection([
        ('5', '5% discount (rate 0.95)'),
        ('10', '10% discount (rate 0.90)'),
        ('15', '15% discount (rate 0.85)'),
        ('20', '20% discount (rate 0.80)'),
        ('25', '25% discount (rate 0.75)'),
        ('30', '30% discount (rate 0.70)'),
        ('35', '35% discount (rate 0.65)'),
        ('40', '40% discount (rate 0.60)'),
        ('50', '50% discount (rate 0.50)'),
    ], string='Quick Discount', help='Select a predefined discount percentage (optional helper field)')
    
    rate = fields.Float(
        string='Discount Rate',
        required=True,
        digits=(5, 4),
        help='Discount rate (e.g., 0.80 means 20% discount from list price)'
    )
    
    discount_percent = fields.Float(
        string='Discount %',
        compute='_compute_discount_percent',
        store=True,
        digits=(5, 2),
        help='Discount percentage calculated from rate (e.g., rate 0.80 = 20% discount)'
    )
    
    valid_from = fields.Date(
        string='Valid From',
        help='Effective date'
    )
    
    valid_to = fields.Date(
        string='Valid To',
        help='Effective end date'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Active flag'
    )
    
    note = fields.Text(
        string='Notes',
        help='Optional notes'
    )
    
    # Computed display name
    display_name_full = fields.Char(
        string='Display Name',
        compute='_compute_display_name_full',
        store=True
    )

    _sql_constraints = [
        ('unique_supplier_maker_active',
         'UNIQUE(supplier_comp_code, maker_name, active) WHERE active = true',
         'Only one active record per supplier and manufacturer is allowed!'),
        ('rate_positive',
         'CHECK(rate > 0 AND rate <= 2.0)',
         'Rate must be between 0 and 2.0!')
    ]

    @api.depends('rate')
    def _compute_discount_percent(self):
        """Calculate discount percentage from rate"""
        for record in self:
            if record.rate:
                # If rate is 0.80, discount is 20%
                record.discount_percent = (1.0 - record.rate) * 100.0
            else:
                record.discount_percent = 0.0

    @api.depends('supplier_comp_code', 'maker_name', 'rate')
    def _compute_display_name_full(self):
        """Compute display name"""
        for record in self:
            record.display_name_full = (
                f"{record.supplier_comp_code} / {record.maker_name} "
                f"(Rate: {record.rate:.4f} = {record.discount_percent:.2f}% discount)"
            )

    @api.model
    def _get_supplier_codes(self):
        """Get list of supplier codes from external mapping"""
        mapping_model = self.env['supplier.external.mapping']
        mappings = mapping_model.search([('active', '=', True)])
        codes = [(m.external_supplier_comp_code, m.external_supplier_comp_code) for m in mappings]
        # Remove duplicates
        codes = list(set(codes))
        codes.sort()
        return codes or [('', '')]

    @api.onchange('supplier_comp_code_selection')
    def _onchange_supplier_code_selection(self):
        """Auto-fill supplier code when selected from dropdown"""
        if self.supplier_comp_code_selection:
            self.supplier_comp_code = self.supplier_comp_code_selection

    @api.onchange('maker_name_selection')
    def _onchange_maker_name_selection(self):
        """Auto-fill maker name when selected from dropdown"""
        if self.maker_name_selection:
            self.maker_name = self.maker_name_selection

    @api.onchange('discount_percent_selection')
    def _onchange_discount_percent_selection(self):
        """Auto-calculate rate when discount percentage is selected"""
        if self.discount_percent_selection:
            discount = float(self.discount_percent_selection)
            self.rate = (100.0 - discount) / 100.0

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_dates(self):
        """Validate date range"""
        for record in self:
            if record.valid_from and record.valid_to:
                if record.valid_from >= record.valid_to:
                    raise ValidationError(_(
                        'Valid From date must be before Valid To date!'
                    ))

    @api.constrains('rate')
    def _check_rate(self):
        """Validate rate value"""
        for record in self:
            if record.rate <= 0 or record.rate > 2.0:
                raise ValidationError(_(
                    'Rate must be between 0.0 and 2.0 (e.g., 0.75, 1.0, 1.20)'
                ))

    def name_get(self):
        """Display name format"""
        result = []
        for record in self:
            name = (
                f"{record.supplier_comp_code} / {record.maker_name} "
                f"(Rate: {record.rate:.4f})"
            )
            result.append((record.id, name))
        return result

    @api.model
    def get_rate(self, supplier_comp_code, maker_name, check_date=None):
        """
        Get manufacturer rate
        
        Args:
            supplier_comp_code: Supplier company code
            maker_name: Manufacturer name
            check_date: Date to check validity (default: today)
            
        Returns:
            float: rate value or False if not found
        """
        if not supplier_comp_code or not maker_name:
            return False
        
        if check_date is None:
            check_date = date.today()
        
        # Search
        domain = [
            ('supplier_comp_code', '=', supplier_comp_code),
            ('maker_name', '=', maker_name),
            ('active', '=', True),
        ]
        
        rate_record = self.search(domain, limit=1)
        
        # Check date validity
        if rate_record:
            if rate_record.valid_from and check_date < rate_record.valid_from:
                _logger.warning(
                    f"Manufacturer rate not yet valid: {supplier_comp_code}/{maker_name}"
                )
                return False
            if rate_record.valid_to and check_date > rate_record.valid_to:
                _logger.warning(
                    f"Manufacturer rate expired: {supplier_comp_code}/{maker_name}"
                )
                return False
            
            _logger.info(
                f"Manufacturer rate found: {supplier_comp_code}/{maker_name} = {rate_record.rate}"
            )
            return rate_record.rate
        
        _logger.debug(
            f"Manufacturer rate not found: {supplier_comp_code}/{maker_name}"
        )
        return False

    @api.model
    def get_discount_percent(self, supplier_comp_code, maker_name, check_date=None):
        """
        Get discount percentage for manufacturer
        
        Args:
            supplier_comp_code: Supplier company code
            maker_name: Manufacturer name
            check_date: Date to check validity (default: today)
            
        Returns:
            float: discount percentage or False if not found
        """
        rate = self.get_rate(supplier_comp_code, maker_name, check_date)
        if rate:
            return (1.0 - rate) * 100.0
        return False
