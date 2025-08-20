from odoo import api, fields, models
from odoo.exceptions import ValidationError

class JPHoliday(models.Model):
    _name = "jp.holiday"
    _description = "Japan Public Holiday"
    _order = "date"

    name = fields.Char(required=True)
    date = fields.Date(required=True, index=True)
    year = fields.Integer(compute="_compute_year", store=True, index=True)

    _sql_constraints = [
        ("uniq_date", "unique(date)", "There is already a holiday on this date."),
    ]

    @api.depends("date")
    def _compute_year(self):
        for rec in self:
            rec.year = rec.date.year if rec.date else False
