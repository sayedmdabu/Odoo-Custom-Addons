from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    customer_ref = fields.Char(string='Customer Reference')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if name:
            domain = ['|', ('name', operator, name), ('customer_ref', operator, name)]
            products = self.search(domain + args, limit=limit)
        else:
            products = self.search(args, limit=limit)
        return products.name_get()
    
    def name_get(self):
        result = []
        for product in self:
            name = product.name
            if product.customer_ref:
                name = f"{product.customer_ref} - {name}"
            result.append((product.id, name))
        return result