# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MonthlyBillingPdfConfig(models.Model):
    _name = 'monthly.billing.pdf.config'
    _description = 'Monthly Billing PDF Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        required=True,
        default='Default PDF Configuration'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    is_default = fields.Boolean(
        string='Default Configuration',
        default=False,
        help='Use this configuration as default for new monthly billings'
    )
    
    # ==================== COLOR SETTINGS ====================
    
    primary_color = fields.Char(
        string='Primary Color',
        default='#2c5aa0',
        help='Main color for headers, borders, and highlights (hex code)'
    )
    
    secondary_color = fields.Char(
        string='Secondary Color',
        default='#5a8fd8',
        help='Secondary accent color (hex code)'
    )
    
    header_border_color = fields.Char(
        string='Header Border Color',
        default='#2c5aa0',
        help='Color of the main header border'
    )
    
    table_header_bg_color = fields.Char(
        string='Table Header Background',
        default='#2c5aa0',
        help='Background color for table headers'
    )
    
    table_header_text_color = fields.Char(
        string='Table Header Text Color',
        default='#ffffff',
        help='Text color for table headers'
    )
    
    amount_box_border_color = fields.Char(
        string='Amount Box Border Color',
        default='#2c5aa0',
        help='Border color for amount summary box'
    )
    
    total_amount_bg_color = fields.Char(
        string='Total Amount Background',
        default='#2c5aa0',
        help='Background color for total amount bar'
    )
    
    info_box_bg_color = fields.Char(
        string='Info Box Background',
        default='#f8f9fa',
        help='Background color for information boxes'
    )
    
    # ==================== LOGO SETTINGS ====================
    
    show_logo = fields.Boolean(
        string='Show Company Logo',
        default=True
    )
    
    logo_position = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ], string='Logo Position', default='left')
    
    logo_max_width = fields.Integer(
        string='Logo Max Width (px)',
        default=200
    )
    
    logo_max_height = fields.Integer(
        string='Logo Max Height (px)',
        default=80
    )
    
    # ==================== HEADER SETTINGS ====================
    
    header_title_en = fields.Char(
        string='Header Title (English)',
        default='Monthly Billing Statement'
    )
    
    header_title_ja = fields.Char(
        string='Header Title (Japanese)',
        default='月次請求書'
    )
    
    show_status_badge = fields.Boolean(
        string='Show Status Badge',
        default=True
    )
    
    header_title_size = fields.Integer(
        string='Header Title Font Size (px)',
        default=28
    )
    
    header_subtitle_size = fields.Integer(
        string='Header Subtitle Font Size (px)',
        default=20
    )
    
    # ==================== SECTION VISIBILITY ====================
    
    show_customer_section = fields.Boolean(
        string='Show Customer Section',
        default=True
    )
    
    show_period_section = fields.Boolean(
        string='Show Period Section',
        default=True
    )
    
    show_amount_summary = fields.Boolean(
        string='Show Amount Summary',
        default=True
    )
    
    show_invoice_details = fields.Boolean(
        string='Show Invoice Details Table',
        default=True
    )
    
    show_notes_section = fields.Boolean(
        string='Show Notes Section',
        default=True
    )
    
    show_payment_info = fields.Boolean(
        string='Show Payment Information',
        default=True
    )
    
    show_contact_info = fields.Boolean(
        string='Show Contact Information',
        default=True
    )
    
    show_footer = fields.Boolean(
        string='Show Footer',
        default=True
    )
    
    # ==================== CUSTOM TEXT ====================
    
    customer_section_title_en = fields.Char(
        string='Customer Section Title (EN)',
        default='Bill To'
    )
    
    customer_section_title_ja = fields.Char(
        string='Customer Section Title (JA)',
        default='請求先'
    )
    
    period_section_title_en = fields.Char(
        string='Period Section Title (EN)',
        default='Billing Period'
    )
    
    period_section_title_ja = fields.Char(
        string='Period Section Title (JA)',
        default='請求期間'
    )
    
    invoice_details_title_en = fields.Char(
        string='Invoice Details Title (EN)',
        default='Invoice Details'
    )
    
    invoice_details_title_ja = fields.Char(
        string='Invoice Details Title (JA)',
        default='請求明細'
    )
    
    payment_info_title_en = fields.Char(
        string='Payment Info Title (EN)',
        default='Payment Information'
    )
    
    payment_info_title_ja = fields.Char(
        string='Payment Info Title (JA)',
        default='お支払い先'
    )
    
    contact_info_title_en = fields.Char(
        string='Contact Info Title (EN)',
        default='Contact Information'
    )
    
    contact_info_title_ja = fields.Char(
        string='Contact Info Title (JA)',
        default='お問い合わせ先'
    )
    
    footer_text_en = fields.Text(
        string='Footer Text (English)',
        default='This document was automatically generated by the Monthly Billing System.'
    )
    
    footer_text_ja = fields.Text(
        string='Footer Text (Japanese)',
        default='本書類は月次請求システムにより自動生成されました。'
    )
    
    # ==================== TABLE SETTINGS ====================
    
    table_show_row_numbers = fields.Boolean(
        string='Show Row Numbers',
        default=True
    )
    
    table_stripe_rows = fields.Boolean(
        string='Stripe Table Rows',
        default=True,
        help='Alternate row background colors'
    )
    
    table_stripe_color = fields.Char(
        string='Table Stripe Color',
        default='#f8f9fa'
    )
    
    table_border_color = fields.Char(
        string='Table Border Color',
        default='#dee2e6'
    )
    
    # ==================== AMOUNT LABELS ====================
    
    subtotal_label_en = fields.Char(
        string='Subtotal Label (EN)',
        default='Subtotal'
    )
    
    subtotal_label_ja = fields.Char(
        string='Subtotal Label (JA)',
        default='税抜合計'
    )
    
    tax_label_en = fields.Char(
        string='Tax Label (EN)',
        default='Tax Amount'
    )
    
    tax_label_ja = fields.Char(
        string='Tax Label (JA)',
        default='消費税'
    )
    
    total_label_en = fields.Char(
        string='Total Label (EN)',
        default='Total Amount'
    )
    
    total_label_ja = fields.Char(
        string='Total Label (JA)',
        default='税込合計'
    )
    
    # ==================== LAYOUT SETTINGS ====================
    
    page_margin_top = fields.Integer(
        string='Page Margin Top (px)',
        default=15
    )
    
    page_margin_bottom = fields.Integer(
        string='Page Margin Bottom (px)',
        default=15
    )
    
    section_spacing = fields.Integer(
        string='Section Spacing (px)',
        default=25
    )
    
    # ==================== FONT SETTINGS ====================
    
    base_font_size = fields.Integer(
        string='Base Font Size (px)',
        default=12
    )
    
    font_family = fields.Selection([
        ('default', 'Default (System)'),
        ('arial', 'Arial'),
        ('helvetica', 'Helvetica'),
        ('times', 'Times New Roman'),
        ('courier', 'Courier'),
    ], string='Font Family', default='default')
    
    # ==================== WATERMARK ====================
    
    show_watermark = fields.Boolean(
        string='Show Watermark',
        default=False
    )
    
    watermark_text = fields.Char(
        string='Watermark Text',
        default='DRAFT'
    )
    
    watermark_opacity = fields.Float(
        string='Watermark Opacity',
        default=0.1,
        help='0.0 = invisible, 1.0 = fully visible'
    )
    
    # ==================== METHODS ====================
    
    @api.model
    def get_default_config(self, company_id=None):
        """Get default configuration for a company"""
        if not company_id:
            company_id = self.env.company.id
        
        config = self.search([
            ('company_id', '=', company_id),
            ('is_default', '=', True),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            # Return first active config or create default
            config = self.search([
                ('company_id', '=', company_id),
                ('active', '=', True)
            ], limit=1)
            
            if not config:
                config = self.create({
                    'name': 'Default Configuration',
                    'company_id': company_id,
                    'is_default': True
                })
        
        return config
    
    @api.constrains('is_default', 'company_id')
    def _check_default_config(self):
        """Ensure only one default config per company"""
        for record in self:
            if record.is_default:
                other_defaults = self.search([
                    ('company_id', '=', record.company_id.id),
                    ('is_default', '=', True),
                    ('id', '!=', record.id)
                ])
                if other_defaults:
                    other_defaults.write({'is_default': False})
    
    def action_set_as_default(self):
        """Set this config as default"""
        self.ensure_one()
        self.write({'is_default': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Configuration set as default'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_preview_pdf(self):
        """Preview PDF with current settings"""
        self.ensure_one()
        # Find a sample monthly billing to preview
        sample_billing = self.env['monthly.billing.header'].search([], limit=1)
        if not sample_billing:
            raise UserError(_('No monthly billing found. Please create one first.'))
        
        return self.env.ref('monthly_billing.action_report_monthly_billing_statement').report_action(
            sample_billing,
            config={
                'pdf_config_id': self.id
            }
        )
