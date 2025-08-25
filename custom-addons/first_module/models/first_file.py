from odoo import models, fields, api


class FirstFile(models.Model):
    _name = 'first.file'
    _description = 'First File'

    name = fields.Char(string="name", required=True)
    description = fields.Text(string="description")