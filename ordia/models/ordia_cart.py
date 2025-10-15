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
        """Search carts from ORDIA API and store in database"""
        self.ensure_one()
        
        # Build URL with parameters
        url = "https://api-staging.bio-purchase.com/ordia/get_carts_ai"
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
            
            # Create or update cart records in database
            cart_ids = []
            for cart_data in cart_list:
                cart_seq = cart_data.get('cart_seq')
                
                # Check if cart already exists
                existing_cart = self.env['ordia.cart'].search([('cart_seq', '=', cart_seq)], limit=1)
                
                cart_values = {
                    'cart_seq': cart_seq,
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
                    'dealer_co_cd': self.dealer_co_cd,
                    'status': self.status,
                }
                
                if existing_cart:
                    # Update existing record
                    existing_cart.write(cart_values)
                    cart_ids.append(existing_cart.id)
                else:
                    # Create new record
                    cart = self.env['ordia.cart'].create(cart_values)
                    cart_ids.append(cart.id)
            
            # Return action to show cart list
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


class OrdiaCart(models.Model):  # Changed from TransientModel to Model for database storage
    _name = 'ordia.cart'
    _description = 'ORDIA Cart'
    _order = 'order_date desc, cart_seq desc'

    # Primary identification
    cart_seq = fields.Integer(string='Cart Seq', required=True, index=True)
    dealer_co_cd = fields.Char(string='Dealer Code', index=True)
    status = fields.Char(string='Status')
    
    # Product information
    maker_name = fields.Char(string='Maker Name')
    item_sku = fields.Char(string='Item SKU', index=True)
    supp_sku = fields.Char(string='Supplier SKU')
    item_name = fields.Char(string='Item Name')
    capacity = fields.Char(string='Capacity')
    kikaku = fields.Char(string='Kikaku')
    manufacturer_sku = fields.Char(string='Manufacturer SKU')
    supplier_system_sku = fields.Char(string='Supplier System SKU')
    volume_unit_label = fields.Char(string='Volume Unit')
    
    # Quantity and pricing
    suryo = fields.Integer(string='Quantity')
    teika_tanka = fields.Float(string='List Price', digits=(12, 2))
    tanka = fields.Float(string='Unit Price', digits=(12, 2))
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True, digits=(12, 2))
    
    # Delivery information
    nonyu_address1 = fields.Char(string='Delivery Address 1')
    nonyu_address2 = fields.Char(string='Delivery Address 2')
    
    # Order and customer information
    order_date = fields.Datetime(string='Order Date', index=True)
    customer_tanto = fields.Char(string='Customer Contact')
    customer_kikanname = fields.Char(string='Customer Organization', index=True)
    customer_sosikiname = fields.Char(string='Customer Department')
    customer_email = fields.Char(string='Customer Email', index=True)
    
    # Audit fields
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)
    
    # SQL constraint to ensure unique cart_seq
    _sql_constraints = [
        ('cart_seq_unique', 'unique(cart_seq)', 'Cart Sequence must be unique!'),
    ]
    
    @api.depends('suryo', 'tanka')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.suryo * record.tanka
    
    def name_get(self):
        """Display cart_seq as name"""
        result = []
        for record in self:
            name = f"Cart #{record.cart_seq}"
            if record.customer_kikanname:
                name += f" - {record.customer_kikanname}"
            result.append((record.id, name))
        return result
    
    def action_refresh_from_api(self):
        """Refresh cart data from API"""
        for record in self:
            # Open search wizard with current cart's dealer code
            return {
                'name': 'Refresh from API',
                'type': 'ir.actions.act_window',
                'res_model': 'ordia.cart.search',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_dealer_co_cd': record.dealer_co_cd,
                    'default_cart_seq': str(record.cart_seq),
                },
            }