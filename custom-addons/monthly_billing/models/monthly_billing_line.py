# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MonthlyBillingLine(models.Model):
    _name = 'monthly.billing.line'
    _description = 'Monthly Billing Line'
    _order = 'sequence, id'

    header_id = fields.Many2one(
        'monthly.billing.header',
        string='Monthly Billing Header',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Original Invoice',
        required=True,
        ondelete='restrict',
        index=True
    )
    
    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Original Invoice Line',
        ondelete='restrict',
        index=True
    )
    
    date_invoice = fields.Date(
        string='Invoice Date',
        related='invoice_id.invoice_date',
        store=True
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        ondelete='restrict'
    )
    
    name = fields.Char(
        string='Description',
        required=True
    )
    
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        digits='Product Unit of Measure'
    )
    
    price_unit = fields.Monetary(
        string='Unit Price',
        required=True
    )
    
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True
    )
    
    tax_id = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]"
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    note = fields.Char(
        string='Note'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='header_id.currency_id',
        store=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='header_id.company_id',
        store=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='header_id.partner_id',
        store=True
    )

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence automatically"""
        for vals in vals_list:
            if 'sequence' not in vals or vals['sequence'] == 10:
                header_id = vals.get('header_id')
                if header_id:
                    last_line = self.search([('header_id', '=', header_id)], order='sequence desc', limit=1)
                    vals['sequence'] = (last_line.sequence + 10) if last_line else 10
        return super(MonthlyBillingLine, self).create(vals_list)
