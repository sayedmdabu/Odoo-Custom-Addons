from odoo import fields, models, api, _

class MyModel(models.Model):
    _name = 'my.module'
    _description = 'My Module Record'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    description = fields.Text()
    date = fields.Date(default=fields.Date.context_today)
    amount = fields.Float()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', tracking=True)

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
