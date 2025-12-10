import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)

class OrdiaCartSearch(models.TransientModel):
    _name = 'ordia.cart.search'
    _description = 'ORDIA Cart Search'

    token = fields.Char(string='Token', required=True)
    dealer_co_cd = fields.Char(string='Dealer Code', required=True)
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
    
    def action_logout(self):
        """Logout - Clear token and redirect to login"""
        self.ensure_one()
        
        # Get current user
        current_user = self.env.user
        
        # Find and clear token for current user
        login_records = self.env['ordia.login'].search([
            ('create_uid', '=', current_user.id)
        ])
        
        if login_records:
            # Clear token and expiry
            login_records.write({
                'token': False,
                'token_expiry': False,
            })
            _logger.info(f"User {current_user.name} logged out from ORDIA")
        
        # Close current wizard and redirect to login form
        return {
            'name': 'ORDIA Login',
            'type': 'ir.actions.act_window',
            'res_model': 'ordia.login',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_username': '',
            },
        }
    
    def action_search_carts(self):
        """Search carts from ORDIA API and store in TEMPORARY model"""
        self.ensure_one()
        
        # Build URL with parameters
        url = "https://ordia-api.bio-purchase.com/ordia/get_carts_ai"
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
            response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            result = response.json()
            cart_list = result.get('cartList', [])
            
            # Delete existing temporary cart records
            self.env['ordia.cart.temp'].search([]).unlink()
            
            # Create TEMPORARY cart records (NOT saved to database yet)
            temp_cart_ids = []
            for cart_data in cart_list:
                cart_values = {
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
                    'dealer_co_cd': self.dealer_co_cd,
                    'api_status': self.status,
                    # Store additional fields if they come from API
                    'dealer_customer_cd': cart_data.get('dealer_customer_cd'),
                    'delivery_date': cart_data.get('delivery_date'),
                    'comment_spp': cart_data.get('comment_spp'),
                }
                
                # Create TEMPORARY record
                temp_cart = self.env['ordia.cart.temp'].create(cart_values)
                temp_cart_ids.append(temp_cart.id)
            
            # Return action to show TEMPORARY cart list
            return {
                'name': f'ORDIA Carts - Temporary ({len(temp_cart_ids)} records)',
                'type': 'ir.actions.act_window',
                'res_model': 'ordia.cart.temp',
                'view_mode': 'list,form',
                'domain': [('id', 'in', temp_cart_ids)],
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


class OrdiaCartTemp(models.TransientModel):
    """Temporary model for API search results - NOT saved to database"""
    _name = 'ordia.cart.temp'
    _description = 'ORDIA Cart Temporary'
    _order = 'order_date desc, cart_seq desc'

    # Primary identification
    cart_seq = fields.Integer(string='Cart Seq', required=True)
    dealer_co_cd = fields.Char(string='Dealer Code')
    api_status = fields.Char(string='API Status')
    
    # Additional fields for sale order creation
    dealer_customer_cd = fields.Char(string='Dealer Customer Code')
    delivery_date = fields.Datetime(string='Delivery Date')
    comment_spp = fields.Text(string='Comment SPP')
    
    # Product information
    maker_name = fields.Char(string='Maker Name')
    item_sku = fields.Char(string='Item SKU')
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
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', digits=(12, 2))
    
    # Delivery information
    nonyu_address1 = fields.Char(string='Delivery Address 1')
    nonyu_address2 = fields.Char(string='Delivery Address 2')
    
    # Order and customer information
    order_date = fields.Datetime(string='Order Date')
    customer_tanto = fields.Char(string='Customer Contact')
    customer_kikanname = fields.Char(string='Customer Organization')
    customer_sosikiname = fields.Char(string='Customer Department')
    customer_email = fields.Char(string='Customer Email')
    
    @api.depends('suryo', 'tanka')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.suryo * record.tanka
    
    def name_get(self):
        """Display cart_seq as name"""
        result = []
        for record in self:
            name = f"Temp Cart #{record.cart_seq}"
            if record.customer_kikanname:
                name += f" - {record.customer_kikanname}"
            result.append((record.id, name))
        return result
    
    def action_save_to_database(self):
        """Save selected temporary carts to permanent database, create products and sale orders"""
        saved_count = 0
        updated_count = 0
        saved_cart_ids = []
        
        # Prepare all order lines data
        order_lines = []
        first_record = None
        cart_seq_list = []  # Collect cart_seq for API update
        
        for temp_record in self:
            # Collect cart_seq
            cart_seq_list.append(temp_record.cart_seq)
            
            # Step 1: Create or update product
            product = self._create_or_update_product(temp_record)
            
            # Store for sale order creation
            order_lines.append({
                'product': product,
                'temp_record': temp_record,
            })
            
            if not first_record:
                first_record = temp_record
            
            # Step 2: Save to permanent ordia.cart model
            OrdiaCart = self.env['ordia.cart']
            
            existing_cart = OrdiaCart.search([('cart_seq', '=', temp_record.cart_seq)], limit=1)
            
            cart_values = {
                'cart_seq': temp_record.cart_seq,
                'maker_name': temp_record.maker_name,
                'item_sku': temp_record.item_sku,
                'supp_sku': temp_record.supp_sku,
                'item_name': temp_record.item_name,
                'capacity': temp_record.capacity,
                'kikaku': temp_record.kikaku,
                'suryo': temp_record.suryo,
                'teika_tanka': temp_record.teika_tanka,
                'tanka': temp_record.tanka,
                'nonyu_address1': temp_record.nonyu_address1,
                'nonyu_address2': temp_record.nonyu_address2,
                'order_date': temp_record.order_date,
                'supplier_system_sku': temp_record.supplier_system_sku,
                'customer_tanto': temp_record.customer_tanto,
                'customer_kikanname': temp_record.customer_kikanname,
                'customer_sosikiname': temp_record.customer_sosikiname,
                'customer_email': temp_record.customer_email,
                'manufacturer_sku': temp_record.manufacturer_sku,
                'volume_unit_label': temp_record.volume_unit_label,
                'dealer_co_cd': temp_record.dealer_co_cd,
                'api_status': temp_record.api_status,
                'state': 'draft',
            }
            
            if existing_cart:
                # Update existing cart
                existing_cart.write(cart_values)
                saved_cart_ids.append(existing_cart.id)
                updated_count += 1
                _logger.info(f"Updated cart_seq: {temp_record.cart_seq}")
            else:
                # Create new cart
                new_cart = OrdiaCart.create(cart_values)
                saved_cart_ids.append(new_cart.id)
                saved_count += 1
                _logger.info(f"Created new cart_seq: {temp_record.cart_seq}")
        
        # Step 3: Create sale order with all lines
        if order_lines and first_record:
            sale_order = self._create_sale_order_from_lines(order_lines)
            
            # Step 4: Update cart status via API (call once with all cart_seq)
            if cart_seq_list:
                self._update_cart_status_api(cart_seq_list, first_record.dealer_co_cd)
        
        # Show success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Save Successful!',
                'message': f'Saved {saved_count} new cart(s) and updated {updated_count} existing cart(s) to database. Total: {len(saved_cart_ids)} cart(s).',
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'ordia.cart',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', saved_cart_ids)],
                    'target': 'current',
                }
            }
        }
    
    def _create_or_update_product(self, temp_record):
        """Create or update product.product record"""
        Product = self.env['product.product']
        
        # Search for existing product by item_sku
        product = Product.search([('default_code', '=', temp_record.item_sku)], limit=1)
        
        # Prepare product values
        product_vals = {
            'name': temp_record.item_name or f"Product {temp_record.item_sku}",
            'default_code': temp_record.item_sku,
            'type': 'product',
            'list_price': temp_record.teika_tanka or 0.0,
            'standard_price': temp_record.tanka or 0.0,
            'description': f"""
Maker: {temp_record.maker_name or ''}
Capacity: {temp_record.capacity or ''}
Kikaku: {temp_record.kikaku or ''}
Supplier SKU: {temp_record.supp_sku or ''}
Manufacturer SKU: {temp_record.manufacturer_sku or ''}
            """.strip(),
        }
        
        if product:
            # Update existing product
            product.write(product_vals)
            _logger.info(f"Updated product: {product.name} (SKU: {temp_record.item_sku})")
        else:
            # Create new product
            product = Product.create(product_vals)
            _logger.info(f"Created new product: {product.name} (SKU: {temp_record.item_sku})")
        
        return product
    
    def _create_sale_order_from_lines(self, line_data):
        """Create a single sale order with all lines from selected carts"""
        if not line_data:
            return None
        
        SaleOrder = self.env['sale.order']
        
        try:
            # Get first record for order header info
            first_temp = line_data[0]['temp_record']
            
            # Find or create partner based on customer email
            partner = self._find_or_create_partner(first_temp)
            
            # Get company
            company = self.env.company
            
            # Get earliest order date from all lines
            order_dates = [ld['temp_record'].order_date for ld in line_data if ld['temp_record'].order_date]
            earliest_date = min(order_dates) if order_dates else fields.Datetime.now()
            
            # Combine all comments
            all_comments = []
            delivery_dates = []
            for ld in line_data:
                if ld['temp_record'].comment_spp:
                    all_comments.append(ld['temp_record'].comment_spp)
                if ld['temp_record'].delivery_date:
                    delivery_dates.append(ld['temp_record'].delivery_date)
            
            # Use earliest delivery date if available
            commitment_date = min(delivery_dates) if delivery_dates else None
            
            # Create sale order
            sale_order_vals = {
                'partner_id': partner.id,
                'company_id': company.id,
                'date_order': earliest_date,
                'state': 'sale',
                'note': '\n'.join(all_comments) if all_comments else '',
            }
            
            # Add commitment_date if available
            if commitment_date:
                sale_order_vals['commitment_date'] = commitment_date
            
            sale_order = SaleOrder.create(sale_order_vals)
            
            # Create sale order lines
            for line_info in line_data:
                product = line_info['product']
                temp_rec = line_info['temp_record']
                
                line_vals = {
                    'order_id': sale_order.id,
                    'product_id': product.id,
                    'name': temp_rec.item_name or product.name,
                    'product_uom_qty': temp_rec.suryo or 1,
                    'price_unit': temp_rec.tanka or 0.0,
                    'company_id': company.id,
                    'state': 'sale',
                }
                
                # Create the order line
                self.env['sale.order.line'].create(line_vals)
            
            # Manually set invoice status after creating lines
            sale_order.order_line.write({'invoice_status': 'no'})
            
            _logger.info(f"Created sale order: {sale_order.name} for partner: {partner.name} with {len(line_data)} lines")
            return sale_order
            
        except Exception as e:
            _logger.error(f"Error creating sale order: {str(e)}")
            raise UserError(f'Failed to create sale order: {str(e)}')
    
    def _find_or_create_partner(self, temp_record):
        """Find or create res.partner based on customer info"""
        Partner = self.env['res.partner']
        
        # Search for existing partner by email
        partner = None
        if temp_record.customer_email:
            partner = Partner.search([('email', '=', temp_record.customer_email)], limit=1)
        
        if not partner and temp_record.customer_kikanname:
            # Search by organization name
            partner = Partner.search([('name', '=', temp_record.customer_kikanname)], limit=1)
        
        if not partner:
            # Create new partner
            partner_vals = {
                'name': temp_record.customer_kikanname or temp_record.customer_email or 'Unknown Customer',
                'email': temp_record.customer_email,
                'comment': f"""
Customer Contact: {temp_record.customer_tanto or ''}
Organization: {temp_record.customer_sosikiname or ''}
                """.strip(),
                'company_type': 'company',
            }
            
            partner = Partner.create(partner_vals)
            _logger.info(f"Created new partner: {partner.name}")
        
        return partner
    
    def _update_cart_status_api(self, cart_seq_list, dealer_co_cd):
        """Update cart status via ORDIA API after saving"""
        
        # Get token from context or login record
        token = self.env.context.get('token')
        if not token:
            # Try to get from login record
            current_user = self.env.user
            login_record = self.env['ordia.login'].search([
                ('create_uid', '=', current_user.id)
            ], limit=1, order='last_login desc')
            
            if login_record and login_record.token:
                token = login_record.token
        
        if not token:
            _logger.warning("No token available for cart status update")
            return
        
        # Build URL with parameters
        url = "https://ordia-api.bio-purchase.com/ordia/update_carts_status"
        
        payload = {
            'token': token,
            'dealer_co_cd': dealer_co_cd,
            'cart_seq': cart_seq_list,  # Send as array
            'status': '3',  # Set to status 3 (or whatever status you want)
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('http') == 200:
                _logger.info(f"Successfully updated cart status for {len(cart_seq_list)} carts")
            else:
                _logger.warning(f"Cart status update returned: {result.get('message')}")
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"Cart status update API Error: {str(e)}")
            # Don't raise error, just log it - order is already created
        except Exception as e:
            _logger.error(f"Cart status update Error: {str(e)}")
            # Don't raise error, just log it - order is already created


class OrdiaCart(models.Model):
    """Permanent model for saved carts in database"""
    _name = 'ordia.cart'
    _description = 'ORDIA Cart'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'order_date desc, cart_seq desc'

    # Primary identification
    cart_seq = fields.Integer(string='Cart Seq', required=True, index=True)
    dealer_co_cd = fields.Char(string='Dealer Code', index=True)
    api_status = fields.Char(string='API Status')
    
    # Processing status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
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
    
    # Notes
    notes = fields.Text(string='Notes')
    
    # Audit fields
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)
    create_uid = fields.Many2one('res.users', string='Created by', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated by', readonly=True)
    
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
    
    # Bulk Actions
    def action_confirm_carts(self):
        """Confirm selected carts"""
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'{len(self)} cart(s) confirmed successfully!',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_process_carts(self):
        """Process selected carts"""
        for record in self:
            if record.state in ['draft', 'confirmed']:
                record.state = 'processing'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Processing',
                'message': f'{len(self)} cart(s) are now being processed!',
                'type': 'info',
                'sticky': False,
            }
        }
    
    def action_mark_done(self):
        """Mark selected carts as done"""
        for record in self:
            if record.state == 'processing':
                record.state = 'done'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Completed',
                'message': f'{len(self)} cart(s) marked as done!',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_cancel_carts(self):
        """Cancel selected carts"""
        for record in self:
            if record.state != 'done':
                record.state = 'cancelled'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cancelled',
                'message': f'{len(self)} cart(s) cancelled!',
                'type': 'warning',
                'sticky': False,
            }
        }