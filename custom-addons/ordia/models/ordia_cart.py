import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class OrdiaCartSearch(models.TransientModel):
    _name = 'ordia.cart.search'
    _description = 'ORDIA Cart Search'

    token = fields.Char(string='Token', required=True)
    dealer_co_cd = fields.Char(string='Dealer Code (kikan_code)', required=True)
    status = fields.Selection([
        ('1', 'Status 1'),
        ('2', 'Status 2'),
        ('3', 'Status 3'),
        ('4', 'Status 4'),
        ('5', 'Status 5'),
        ('6', 'Status 6'),
        ('7', 'Status 7'),
        ('8', 'Status 8'),
    ], string='Status', default='7')
    
    cart_seq = fields.Char(string='Cart Sequence')
    item_sku = fields.Char(string='Item SKU')
    customer_email = fields.Char(string='Customer Email')
    
    def action_search_carts(self):
        """Search carts from ORDIA API"""
        self.ensure_one()
        
        # Build URL with parameters
        url = f"https://api-staging.bio-purchase.com/ordia/get_carts_ai"
        params = {
            'token': self.token,
            'dealer_co_cd': self.dealer_co_cd,
            'status': self.status or '7',
        }
        
        if self.cart_seq:
            params['cart_seq'] = self.cart_seq
        if self.item_sku:
            params['item_sku'] = self.item_sku
        if self.customer_email:
            params['customer_email'] = self.customer_email
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            cart_list = result.get('cartList', [])
            
            # Delete existing cart records for this session
            self.env['ordia.cart'].search([]).unlink()
            
            # Create cart records
            cart_ids = []
            for cart_data in cart_list:
                cart = self.env['ordia.cart'].create({
                    'cart_seq': cart_data.get('cart_seq'),
                    'maker_name': cart_data.get('maker_name'),
                    'item_sku': cart_data.get('item_sku'),
                    'supp_sku': cart_data.get('supp_sku'),
                    'item_name': cart_data.get('item_name'),
                    'capacity': cart_data.get('capacity'),
                    'kikaku': cart_data.get('kikaku'),
                    'suryo': cart_data.get('suryo'),
                    'teika_tanka': cart_data.get('teika_tanka'),
                    'tanka': cart_data.get('tanka'),
                    'nonyu_address1': cart_data.get('nonyu_address1'),
                    'nonyu_address2': cart_data.get('nonyu_address2'),
                    'order_date': cart_data.get('order_date'),
                    'supplier_system_sku': cart_data.get('supplier_system_sku'),
                    'customer_tanto': cart_data.get('customer_tanto'),
                    'customer_kikanname': cart_data.get('customer_kikanname'),
                    'customer_sosikiname': cart_data.get('customer_sosikiname'),
                    'customer_email': cart_data.get('customer_email'),
                    'manufacturer_sku': cart_data.get('manufacturer_sku'),
                    'volume_unit_label': cart_data.get('volume_unit_label'),
                })
                cart_ids.append(cart.id)
            
            # Return action to show cart list (Changed 'tree' to 'list' for Odoo 18)
            return {
                'name': f'ORDIA Carts ({len(cart_ids)} records)',
                'type': 'ir.actions.act_window',
                'res_model': 'ordia.cart',
                'view_mode': 'list,form',
                'domain': [('id', 'in', cart_ids)],
                'context': {
                    'search_default_group_by_maker': 1,
                    'token': self.token,
                    'dealer_co_cd': self.dealer_co_cd,
                },
                'target': 'current',
            }
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"ORDIA API Error: {str(e)}")
            raise UserError(f'Connection error: {str(e)}')
        except Exception as e:
            _logger.error(f"Search Error: {str(e)}")
            raise UserError(f'Search failed: {str(e)}')
    
    def action_open_new_search(self):
        """Open a new search dialog"""
        return {
            'name': 'Search Carts',
            'type': 'ir.actions.act_window',
            'res_model': 'ordia.cart.search',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_token': self.token,
                'default_dealer_co_cd': self.dealer_co_cd,
            },
        }


class OrdiaCart(models.TransientModel):
    _name = 'ordia.cart'
    _description = 'ORDIA Cart'
    _order = 'order_date desc, cart_seq desc'

    cart_seq = fields.Integer(string='Cart Seq', readonly=True)
    maker_name = fields.Char(string='Maker Name', readonly=True)
    item_sku = fields.Char(string='Item SKU', readonly=True)
    supp_sku = fields.Char(string='Supplier SKU', readonly=True)
    item_name = fields.Char(string='Item Name', readonly=True)
    capacity = fields.Char(string='Capacity', readonly=True)
    kikaku = fields.Char(string='Kikaku', readonly=True)
    suryo = fields.Integer(string='Quantity', readonly=True)
    teika_tanka = fields.Float(string='List Price', readonly=True)
    tanka = fields.Float(string='Unit Price', readonly=True)
    nonyu_address1 = fields.Char(string='Delivery Address 1', readonly=True)
    nonyu_address2 = fields.Char(string='Delivery Address 2', readonly=True)
    order_date = fields.Datetime(string='Order Date', readonly=True)
    supplier_system_sku = fields.Char(string='Supplier System SKU', readonly=True)
    customer_tanto = fields.Char(string='Customer Contact', readonly=True)
    customer_kikanname = fields.Char(string='Customer Organization', readonly=True)
    customer_sosikiname = fields.Char(string='Customer Department', readonly=True)
    customer_email = fields.Char(string='Customer Email', readonly=True)
    manufacturer_sku = fields.Char(string='Manufacturer SKU', readonly=True)
    volume_unit_label = fields.Char(string='Volume Unit', readonly=True)
    
    # Computed field for total
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', readonly=True)
    
    @api.depends('suryo', 'tanka')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.suryo * record.tanka