# -*- coding: utf-8 -*-
from odoo import api, fields, models

class Ec250ApiSearchResult(models.TransientModel):
    _name = "ec250.api.search.result"
    _description = "EC250 API Search Result"

    wizard_id = fields.Many2one(
        "ec250.api.search.wizard", 
        string="Wizard",
        required=True,
        ondelete="cascade"
    )
    
    # Product fields
    ext_id = fields.Char(string="External ID", readonly=True)
    sku = fields.Char(string="SKU", readonly=True)
    supplier_sku = fields.Char(string="Supplier SKU", readonly=True)
    supplier_comp_code = fields.Char(string="Supplier Company Code", readonly=True)
    supplier_maker_code = fields.Char(string="Supplier Maker Code", readonly=True)
    sales_origin_maker_name = fields.Char(string="Sales Origin Maker", readonly=True)
    maker_name = fields.Char(string="Maker", readonly=True)
    name_jp = fields.Char(string="Name (JP)", readonly=True)
    name = fields.Char(string="Product Name", readonly=True)
    volume_unit_label = fields.Char(string="Volume/Unit", readonly=True)
    list_price = fields.Float(string="List Price", readonly=True, digits=(10, 2))
    
    def action_select_single(self):
        """Select this product and add to order line"""
        self.ensure_one()
        
        if self.wizard_id.sale_order_line_id:
            # Find or create product
            product = self._get_or_create_product()
            
            # Update the sale order line
            self.wizard_id.sale_order_line_id.product_id = product
            
            # Optionally update the price
            if self.list_price > 0:
                self.wizard_id.sale_order_line_id.price_unit = self.list_price
        
        # Close the wizard
        return {'type': 'ir.actions.act_window_close'}
    
    def _get_or_create_product(self):
        """Find existing product or create new one"""
        Product = self.env['product.product']
        
        # Search by SKU
        if self.sku:
            product = Product.search([('default_code', '=', self.sku)], limit=1)
            if product:
                return product
        
        # Create new product
        vals = {
            'name': self.name or self.name_jp or f"Product {self.sku}",
            'default_code': self.sku,
            'list_price': self.list_price,
            'type': 'product',
            'sale_ok': True,
            'purchase_ok': True,
        }
        
        # Add description
        description_parts = []
        if self.supplier_sku:
            description_parts.append(f"Supplier SKU: {self.supplier_sku}")
        if self.maker_name:
            description_parts.append(f"Maker: {self.maker_name}")
        if self.volume_unit_label:
            description_parts.append(f"Volume/Unit: {self.volume_unit_label}")
        
        if description_parts:
            vals['description_sale'] = '\n'.join(description_parts)
        
        return Product.create(vals)