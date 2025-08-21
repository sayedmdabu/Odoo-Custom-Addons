# -*- coding: utf-8 -*-
from odoo import api, fields, models

class JPHolidayFilterWizard(models.TransientModel):
    _name = "jp.holiday.filter.wizard"
    _description = "Filter JP Holidays by Year"

    year = fields.Integer(string="Year", required=True, default=lambda self: fields.Date.today().year)

    def action_apply_filter(self):
        """Return an action opening the jp.holiday list filtered by selected year."""
        self.ensure_one()
        domain = [('year', '=', self.year)]
        # If you have a specific list view you want to use, reference it below.
        return {
            "type": "ir.actions.act_window",
            "name": f"Japan Holidays ({self.year})",
            "res_model": "jp.holiday",
            "view_mode": "list,form",
            "domain": domain,
            "target": "current",
            # keep context handy if you have default_year or search defaults
            "context": {
                "default_year": self.year,
                "search_default_current_year": 0,  # don't auto-override our domain
            },
        }
