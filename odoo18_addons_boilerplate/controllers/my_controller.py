from odoo import http
from odoo.http import request

class MyController(http.Controller):

    @http.route(['/my_module/hello'], type='http', auth='public', website=True)
    def hello(self, **kwargs):
        return "<h1>Hello from My Module (Odoo 18)!</h1>"
