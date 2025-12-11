# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar


class MonthlyBillingGenerateWizard(models.TransientModel):
    _name = 'monthly.billing.generate.wizard'
    _description = 'Monthly Billing Generation Wizard'

    closing_year_month = fields.Char(
        string='Closing Year/Month',
        required=True,
        default=lambda self: self._default_closing_year_month(),
        help='Format: YYYY-MM (e.g., 2025-10)'
    )
    
    closing_day = fields.Integer(
        string='Closing Day',
        required=True,
        default=31,
        help='1-31, where 31 = End of Month'
    )
    
    partner_ids = fields.Many2many(
        'res.partner',
        string='Target Customers',
        domain=[('customer_rank', '>', 0)],
        help='Leave empty to process all customers with invoices in the period'
    )
    
    invoice_state_filter = fields.Selection([
        ('posted', 'Posted Only'),
        ('posted_and_draft', 'Posted and Draft'),
    ], string='Invoice Status Filter', default='posted', required=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    show_preview = fields.Boolean(
        string='Show Preview',
        default=False
    )
    
    dry_run = fields.Boolean(
        string='Dry Run (Preview Only)',
        default=False,
        help='Generate preview without creating records in database'
    )
    
    # Preview fields
    preview_html = fields.Html(
        string='Preview',
        readonly=True
    )
    
    period_start_date = fields.Date(
        string='Calculated Period Start',
        compute='_compute_period_dates',
        readonly=True
    )
    
    period_end_date = fields.Date(
        string='Calculated Period End',
        compute='_compute_period_dates',
        readonly=True
    )
    
    estimated_invoice_count = fields.Integer(
        string='Estimated Invoice Count',
        compute='_compute_estimated_counts',
        readonly=True
    )
    
    estimated_customer_count = fields.Integer(
        string='Estimated Customer Count',
        compute='_compute_estimated_counts',
        readonly=True
    )

    @api.model
    def _default_closing_year_month(self):
        """Default to current year-month"""
        return datetime.now().strftime('%Y-%m')

    @api.depends('closing_year_month', 'closing_day')
    def _compute_period_dates(self):
        """Calculate period start and end dates based on closing logic"""
        for wizard in self:
            if wizard.closing_year_month and wizard.closing_day:
                try:
                    start_date, end_date = self._calculate_period_dates(
                        wizard.closing_year_month,
                        wizard.closing_day
                    )
                    wizard.period_start_date = start_date
                    wizard.period_end_date = end_date
                except Exception:
                    wizard.period_start_date = False
                    wizard.period_end_date = False
            else:
                wizard.period_start_date = False
                wizard.period_end_date = False

    @api.depends('period_start_date', 'period_end_date', 'partner_ids', 'invoice_state_filter', 'company_id')
    def _compute_estimated_counts(self):
        """Compute estimated counts for preview"""
        for wizard in self:
            if wizard.period_start_date and wizard.period_end_date:
                domain = wizard._get_invoice_domain()
                invoices = self.env['account.move'].search(domain)
                wizard.estimated_invoice_count = len(invoices)
                wizard.estimated_customer_count = len(invoices.mapped('partner_id'))
            else:
                wizard.estimated_invoice_count = 0
                wizard.estimated_customer_count = 0

    def _calculate_period_dates(self, closing_year_month, closing_day):
        """
        Calculate period start and end dates based on closing logic.
        
        Logic:
        - If closing_day == 31: Period is from 1st to last day of the month
        - If closing_day < 31: Period is from (previous month's closing_day + 1) to current month's closing_day
        
        Args:
            closing_year_month (str): Format 'YYYY-MM'
            closing_day (int): Closing day (1-31)
            
        Returns:
            tuple: (start_date, end_date)
        """
        try:
            year, month = map(int, closing_year_month.split('-'))
        except ValueError:
            raise ValidationError(_('Invalid closing year/month format. Use YYYY-MM (e.g., 2025-10)'))
        
        if closing_day < 1 or closing_day > 31:
            raise ValidationError(_('Closing day must be between 1 and 31.'))
        
        if closing_day == 31:
            # End of month closing
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)
        else:
            # Specific day closing
            # End date: Current month's closing day
            try:
                end_date = date(year, month, closing_day)
            except ValueError:
                # Handle case where closing_day doesn't exist in the month (e.g., Feb 30)
                last_day = calendar.monthrange(year, month)[1]
                end_date = date(year, month, min(closing_day, last_day))
            
            # Start date: Previous month's closing day + 1
            prev_month_date = date(year, month, 1) - relativedelta(days=1)
            prev_year = prev_month_date.year
            prev_month = prev_month_date.month
            
            try:
                prev_closing_date = date(prev_year, prev_month, closing_day)
            except ValueError:
                # Handle case where closing_day doesn't exist in previous month
                last_day = calendar.monthrange(prev_year, prev_month)[1]
                prev_closing_date = date(prev_year, prev_month, min(closing_day, last_day))
            
            start_date = prev_closing_date + relativedelta(days=1)
        
        return start_date, end_date

    def _get_invoice_domain(self):
        """Build domain for invoice search"""
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', self.period_start_date),
            ('invoice_date', '<=', self.period_end_date),
        ]
        
        # Filter by state
        if self.invoice_state_filter == 'posted':
            domain.append(('state', '=', 'posted'))
        else:
            domain.append(('state', 'in', ['draft', 'posted']))
        
        # Filter by partners if specified
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        
        return domain

    def action_preview_target(self):
        """Preview target invoices and customers"""
        self.ensure_one()
        
        if not self.period_start_date or not self.period_end_date:
            raise UserError(_('Please specify valid closing year/month and closing day.'))
        
        domain = self._get_invoice_domain()
        invoices = self.env['account.move'].search(domain)
        
        # Group by partner
        partners_data = {}
        for invoice in invoices:
            partner = invoice.partner_id
            if partner.id not in partners_data:
                partners_data[partner.id] = {
                    'partner': partner,
                    'invoices': self.env['account.move'],
                    'total_amount': 0.0,
                }
            partners_data[partner.id]['invoices'] |= invoice
            partners_data[partner.id]['total_amount'] += invoice.amount_total
        
        # Generate preview HTML
        preview_html = self._generate_preview_html(partners_data, invoices)
        self.preview_html = preview_html
        self.show_preview = True
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.billing.generate.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def _generate_preview_html(self, partners_data, invoices):
        """Generate HTML preview of what will be generated"""
        html = """
        <div class="container">
            <h3>Generation Preview</h3>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Period:</strong> %s to %s</p>
                    <p><strong>Total Invoices:</strong> %d</p>
                    <p><strong>Total Customers:</strong> %d</p>
                </div>
            </div>
            <hr/>
            <h4>Customers Summary:</h4>
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Invoice Count</th>
                        <th>Total Amount</th>
                    </tr>
                </thead>
                <tbody>
        """ % (
            self.period_start_date.strftime('%Y-%m-%d'),
            self.period_end_date.strftime('%Y-%m-%d'),
            len(invoices),
            len(partners_data)
        )
        
        for partner_id, data in partners_data.items():
            html += """
                <tr>
                    <td>%s</td>
                    <td>%d</td>
                    <td>%.2f</td>
                </tr>
            """ % (
                data['partner'].name,
                len(data['invoices']),
                data['total_amount']
            )
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html

    def action_generate_monthly_billing(self):
        """Generate monthly billing records"""
        self.ensure_one()
        
        if not self.period_start_date or not self.period_end_date:
            raise UserError(_('Please specify valid closing year/month and closing day.'))
        
        if self.dry_run:
            # Just show preview
            return self.action_preview_target()
        
        # Search for invoices
        domain = self._get_invoice_domain()
        invoices = self.env['account.move'].search(domain)
        
        if not invoices:
            raise UserError(_('No invoices found for the specified period and criteria.'))
        
        # Group invoices by partner
        partners_invoices = {}
        for invoice in invoices:
            partner = invoice.partner_id
            if partner.id not in partners_invoices:
                partners_invoices[partner.id] = self.env['account.move']
            partners_invoices[partner.id] |= invoice
        
        # Create monthly billing headers
        created_headers = self.env['monthly.billing.header']
        
        for partner_id, partner_invoices in partners_invoices.items():
            partner = self.env['res.partner'].browse(partner_id)
            
            # Prepare header values
            header_vals = {
                'partner_id': partner.id,
                'period_start_date': self.period_start_date,
                'period_end_date': self.period_end_date,
                'closing_year_month': self.closing_year_month,
                'closing_day': self.closing_day,
                'company_id': self.company_id.id,
                'currency_id': self.company_id.currency_id.id,
            }
            
            # Set closing type based on closing day
            if self.closing_day == 31:
                header_vals['closing_type'] = 'end_of_month'
            elif self.closing_day == 20:
                header_vals['closing_type'] = 'day_20'
            elif self.closing_day == 15:
                header_vals['closing_type'] = 'day_15'
            elif self.closing_day == 10:
                header_vals['closing_type'] = 'day_10'
            else:
                header_vals['closing_type'] = 'custom'
            
            # Create header
            header = self.env['monthly.billing.header'].create(header_vals)
            created_headers |= header
            
            # Create lines from invoice lines
            line_vals_list = []
            sequence = 10
            
            for invoice in partner_invoices:
                for inv_line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                    line_vals = {
                        'header_id': header.id,
                        'invoice_id': invoice.id,
                        'invoice_line_id': inv_line.id,
                        'product_id': inv_line.product_id.id if inv_line.product_id else False,
                        'name': inv_line.name or inv_line.product_id.name or '',
                        'quantity': inv_line.quantity,
                        'price_unit': inv_line.price_unit,
                        'tax_id': [(6, 0, inv_line.tax_ids.ids)],
                        'sequence': sequence,
                        'note': invoice.name or '',
                    }
                    line_vals_list.append(line_vals)
                    sequence += 10
            
            # Batch create lines for performance
            if line_vals_list:
                self.env['monthly.billing.line'].create(line_vals_list)
        
        # Return action to view created records
        return {
            'name': _('Generated Monthly Billings'),
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.billing.header',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_headers.ids)],
            'context': {
                'search_default_group_by_partner': 1,
            },
        }

    @api.constrains('closing_year_month')
    def _check_closing_year_month(self):
        """Validate closing year/month format"""
        for wizard in self:
            if wizard.closing_year_month:
                try:
                    datetime.strptime(wizard.closing_year_month, '%Y-%m')
                except ValueError:
                    raise ValidationError(_('Closing Year/Month must be in format YYYY-MM (e.g., 2025-10)'))

    @api.constrains('closing_day')
    def _check_closing_day(self):
        """Validate closing day"""
        for wizard in self:
            if wizard.closing_day < 1 or wizard.closing_day > 31:
                raise ValidationError(_('Closing day must be between 1 and 31.'))
