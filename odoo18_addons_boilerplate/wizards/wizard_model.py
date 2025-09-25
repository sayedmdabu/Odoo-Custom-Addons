from odoo import fields, models, api, _

class MyWizard(models.TransientModel):
    _name = 'my.module.wizard'
    _description = 'My Module Wizard'

    name = fields.Char(string='Title', required=True)
    note = fields.Text()

    def action_apply(self):
        # Example: create a record
        self.env['my.module'].create({
            'name': self.name,
            'description': self.note,
            'state': 'confirm',
        })
        return {'type': 'ir.actions.act_window_close'}
