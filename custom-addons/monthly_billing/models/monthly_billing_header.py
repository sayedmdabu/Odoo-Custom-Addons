# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar


class MonthlyBillingHeader(models.Model):
    _name = 'monthly.billing.header'
    _description = 'Monthly Billing Header'
    _order = 'closing_year_month desc, name desc'

    name = fields.Char(
        string='Monthly Invoice Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    
    billing_address_id = fields.Many2one(
        'res.partner',
        string='Billing Address',
        compute='_compute_billing_address',
        store=True
    )
    
    billing_group_code = fields.Char(
        string='Billing Group Code',
        related='partner_id.billing_group_code',
        store=True
    )
    
    period_start_date = fields.Date(
        string='Period Start Date',
        required=True,
        tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    
    period_end_date = fields.Date(
        string='Period End Date',
        required=True,
        tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    
    closing_year_month = fields.Char(
        string='Closing Year/Month',
        size=7,
        required=True,
        tracking=True,
        help='Format: YYYY-MM (e.g., 2025-10)'
    )
    
    closing_day = fields.Integer(
        string='Closing Day',
        required=True,
        default=31,
        tracking=True,
        help='1-31, where 31 = End of Month'
    )
    
    closing_type = fields.Selection([
        ('end_of_month', 'End of Month'),
        ('day_20', '20th of Month'),
        ('day_15', '15th of Month'),
        ('day_10', '10th of Month'),
        ('custom', 'Custom'),
    ], string='Closing Type', default='end_of_month', tracking=True)
    
    total_amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_amounts',
        store=True,
        tracking=True
    )
    
    total_amount_tax = fields.Monetary(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True,
        tracking=True
    )
    
    total_amount_total = fields.Monetary(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    
    invoice_line_ids = fields.One2many(
        'monthly.billing.line',
        'header_id',
        string='Invoice Lines',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )
    
    memo = fields.Text(
        string='Notes'
    )
    
    report_printed = fields.Boolean(
        string='PDF Printed',
        default=False,
        copy=False
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count'
    )
    
    date_created = fields.Datetime(
        string='Created Date',
        default=fields.Datetime.now,
        readonly=True
    )
    
    date_confirmed = fields.Datetime(
        string='Confirmed Date',
        readonly=True
    )
    
    date_done = fields.Datetime(
        string='Done Date',
        readonly=True
    )
    
    pdf_config_id = fields.Many2one(
        'monthly.billing.pdf.config',
        string='PDF Configuration',
        help='PDF template configuration for this billing. Leave empty to use default.'
    )

    @api.depends('partner_id')
    def _compute_billing_address(self):
        for record in self:
            if record.partner_id:
                record.billing_address_id = record.partner_id.address_get(['invoice'])['invoice']
            else:
                record.billing_address_id = False

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.tax_id')
    def _compute_amounts(self):
        for record in self:
            total_untaxed = sum(line.price_subtotal for line in record.invoice_line_ids)
            total_tax = 0.0
            
            # Calculate tax for each line
            for line in record.invoice_line_ids:
                if line.tax_id:
                    # Use Odoo's tax computation
                    taxes = line.tax_id.compute_all(
                        line.price_unit,
                        currency=record.currency_id,
                        quantity=line.quantity,
                        product=line.product_id,
                        partner=record.partner_id
                    )
                    total_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
            
            record.total_amount_untaxed = total_untaxed
            record.total_amount_tax = total_tax
            record.total_amount_total = total_untaxed + total_tax

    @api.depends('invoice_line_ids.invoice_id')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_line_ids.mapped('invoice_id'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('monthly.billing.header') or _('New')
        return super(MonthlyBillingHeader, self).create(vals_list)

    def action_confirm(self):
        """Confirm the monthly billing"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft billings can be confirmed.'))
            if not record.invoice_line_ids:
                raise UserError(_('Cannot confirm billing without invoice lines.'))
            record.write({
                'state': 'confirmed',
                'date_confirmed': fields.Datetime.now()
            })

    def action_done(self):
        """Mark the monthly billing as done"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Only confirmed billings can be marked as done.'))
            record.write({
                'state': 'done',
                'date_done': fields.Datetime.now()
            })

    def action_cancel(self):
        """Cancel the monthly billing"""
        for record in self:
            if record.state == 'done':
                raise UserError(_('Cannot cancel a done billing.'))
            record.write({'state': 'cancel'})

    def action_draft(self):
        """Reset to draft"""
        for record in self:
            if record.state != 'cancel':
                raise UserError(_('Only cancelled billings can be reset to draft.'))
            record.write({
                'state': 'draft',
                'date_confirmed': False,
                'date_done': False
            })

    def action_print_report(self):
        """Print the monthly billing statement"""
        self.ensure_one()
        self.write({'report_printed': True})
        
        # Get PDF configuration
        pdf_config = self.pdf_config_id or self.env['monthly.billing.pdf.config'].get_default_config(self.company_id.id)
        
        # Pass config in context
        return self.env.ref('monthly_billing.action_report_monthly_billing_statement').with_context(
            pdf_config_id=pdf_config.id
        ).report_action(self)

    def action_view_invoices(self):
        """View related invoices"""
        self.ensure_one()
        invoice_ids = self.invoice_line_ids.mapped('invoice_id').ids
        return {
            'name': _('Related Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'create': False}
        }

    @api.constrains('closing_year_month')
    def _check_closing_year_month(self):
        """Validate closing year/month format"""
        for record in self:
            if record.closing_year_month:
                try:
                    datetime.strptime(record.closing_year_month, '%Y-%m')
                except ValueError:
                    raise ValidationError(_('Closing Year/Month must be in format YYYY-MM (e.g., 2025-10)'))

    @api.constrains('closing_day')
    def _check_closing_day(self):
        """Validate closing day"""
        for record in self:
            if record.closing_day < 1 or record.closing_day > 31:
                raise ValidationError(_('Closing day must be between 1 and 31.'))

    @api.constrains('period_start_date', 'period_end_date')
    def _check_period_dates(self):
        """Validate period dates"""
        for record in self:
            if record.period_start_date and record.period_end_date:
                if record.period_start_date > record.period_end_date:
                    raise ValidationError(_('Period start date must be before or equal to period end date.'))
