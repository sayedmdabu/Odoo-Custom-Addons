# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Monthly Billing Settings
    monthly_billing_closing_day = fields.Integer(
        string='Closing Day',
        default=31,
        help='Closing day for monthly billing (1-31, 31 = End of Month)'
    )
    monthly_billing_closing_type = fields.Selection([
        ('end_of_month', 'End of Month'),
        ('day_20', '20th of Month'),
        ('day_15', '15th of Month'),
        ('day_10', '10th of Month'),
        ('custom', 'Custom'),
    ], string='Closing Type', default='end_of_month')
    
    billing_group_code = fields.Char(
        string='Billing Group Code',
        help='Group code for consolidated billing'
    )
    
    monthly_billing_ids = fields.One2many(
        'monthly.billing.header',
        'partner_id',
        string='Monthly Billings'
    )
    
    monthly_billing_count = fields.Integer(
        string='Monthly Billing Count',
        compute='_compute_monthly_billing_count'
    )
    
    @api.depends('monthly_billing_ids')
    def _compute_monthly_billing_count(self):
        for partner in self:
            partner.monthly_billing_count = len(partner.monthly_billing_ids)
    
    def action_view_monthly_billings(self):
        """Smart button action to view monthly billings"""
        self.ensure_one()
        return {
            'name': 'Monthly Billings',
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.billing.header',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }
