from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_external_company_cod = fields.Char(
        string='ORDIA Corporate Code',
        help='External company code for ORDIA integration',
        copy=False,
        tracking=True,
    )