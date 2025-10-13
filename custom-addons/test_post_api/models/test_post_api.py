from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TestPostApi(models.Model):
    _name = 'test.post.api'
    _description = 'Test Post API'
    _table = 'test_post_api'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(
        string='Name', 
        required=True,
        help='Full name of the person'
    )
    email = fields.Char(
        string='Email',
        help='Email address'
    )
    phone = fields.Char(
        string='Phone',
        help='Contact phone number'
    )
    note = fields.Text(
        string='Note',
        help='Additional notes or comments'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Audit fields
    create_date = fields.Datetime(
        string='Created Date',
        readonly=True
    )
    write_date = fields.Datetime(
        string='Last Updated',
        readonly=True
    )

    @api.constrains('email')
    def _check_email(self):
        """Validate email format"""
        for record in self:
            if record.email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.email):
                    raise ValidationError('Invalid email format!')

    def _get_record_info(self):
        """Return record information as dictionary"""
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email or '',
            'phone': self.phone or '',
            'note': self.note or '',
            'active': self.active,
            'created_date': self.create_date.strftime('%Y-%m-%d %H:%M:%S') if self.create_date else '',
        }