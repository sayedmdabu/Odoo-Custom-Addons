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
            
            # Step 2: Save cart to permanent storage
            existing_cart = self.env['ordia.cart'].search([('cart_seq', '=', temp_record.cart_seq)], limit=1)
            
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
            }
            
            if existing_cart:
                existing_cart.write(cart_values)
                updated_count += 1
                saved_cart_ids.append(existing_cart.id)
            else:
                new_cart = self.env['ordia.cart'].create(cart_values)
                saved_count += 1
                saved_cart_ids.append(new_cart.id)
            
            # Step 3: Collect order line data
            order_lines.append({
                'product': product,
                'temp_record': temp_record
            })
            
            # Keep the first record for order header information
            if not first_record:
                first_record = temp_record
        
        # Step 4: Create a single sale order with all lines
        if first_record and order_lines:
            # Get token from context
            token = self.env.context.get('token', '')
            
            _logger.info(f"Creating sale order for {len(order_lines)} lines")
            _logger.info(f"Token from context: {'Present' if token else 'Missing'}")
            _logger.info(f"Cart sequences to update: {cart_seq_list}")
            
            sale_order = self._create_sale_order(first_record, order_lines)
            
            if sale_order:
                _logger.info(f"Sale order created successfully: {sale_order.name}")
                
                # Step 5: Update ERP flag in ORDIA API for selected carts only
                if token and cart_seq_list:
                    _logger.info(f"Calling ERP flag update for {len(cart_seq_list)} selected carts")
                    update_result = self._update_erp_flag(token, cart_seq_list)
                    if update_result:
                        _logger.info("ERP flag update completed successfully")
                    else:
                        _logger.warning("ERP flag update failed or returned error")
                else:
                    if not token:
                        _logger.error("Cannot update ERP flag: Token is missing from context")
                    if not cart_seq_list:
                        _logger.error("Cannot update ERP flag: No cart sequences to update")
                
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order',
                    'view_mode': 'form',
                    'res_id': sale_order.id,
                    'name': f'✓ Created Sale Order with {len(order_lines)} lines',
                    'target': 'current',
                }
            else:
                _logger.error("Failed to create sale order")
        
        # Fallback to showing saved carts if no sale order created
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ordia.cart',
            'view_mode': 'list,form',
            'name': f'✓ Saved: {saved_count} new, {updated_count} updated',
            'domain': [('id', 'in', saved_cart_ids)],
            'target': 'current',
        }
    
    def _update_erp_flag(self, token, cart_seq_list):
        """Update ERP flag in ORDIA API after successful sale order creation"""
        try:
            url = f"https://ordia-api.bio-purchase.com/ordia/post_ai_carts_erp_flag_update?token={token}"
            
            # Prepare payload with only selected cart sequences
            post_ai_carts = []
            for cart_seq in cart_seq_list:
                post_ai_carts.append({
                    "cart_seq": cart_seq,
                    "erp_flag": 1
                })
            
            payload = {
                "post_ai_carts": post_ai_carts
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            _logger.info(f"=== ERP Flag Update START ===")
            _logger.info(f"URL: {url}")
            _logger.info(f"Updating ERP flag for {len(cart_seq_list)} cart sequences: {cart_seq_list}")
            _logger.info(f"Payload: {payload}")
            
            # Make POST request with verify=False to handle self-signed certificates
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=30, 
                verify=False  # Ignore SSL certificate verification
            )
            response.raise_for_status()
            
            result = response.json()
            _logger.info(f"ERP flag update response: {result}")
            
            # Check if update was successful
            if result.get('http') == 200:
                _logger.info(f"✓ Successfully updated ERP flag for {len(cart_seq_list)} carts")
                return True
            else:
                _logger.warning(f"ERP flag update returned status: {result.get('http')}, message: {result.get('message')}")
                return False
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"❌ Error updating ERP flag (RequestException): {str(e)}")
            _logger.error(f"Response content: {e.response.text if hasattr(e, 'response') and e.response else 'No response'}")
            # Don't raise error - we don't want to block the sale order creation
            return False
        except Exception as e:
            _logger.error(f"❌ Unexpected error updating ERP flag: {str(e)}")
            import traceback
            _logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't raise error - we don't want to block the sale order creation
            return False
        finally:
            _logger.info(f"=== ERP Flag Update END ===")

    
    def _create_or_update_product(self, temp_record):
        """Create or update product properly using product.template and product.product structure"""
        ProductTemplate = self.env['product.template']
        ProductProduct = self.env['product.product']
        
        # Search for existing product variant by default_code (item_sku)
        existing_product = ProductProduct.search([('default_code', '=', temp_record.item_sku)], limit=1)
        
        if existing_product:
            # Update existing product's template
            template_vals = {
                'name': temp_record.item_name or existing_product.name,
                'list_price': temp_record.teika_tanka or 0.0,
                'standard_price': temp_record.tanka or 0.0,  # Cost price
                'type': 'consu',  # Consumable product
                'sale_ok': True,
                'purchase_ok': True,
                'api_sku' : temp_record.item_sku,
                'api_supplier_sku' : temp_record.supp_sku,
                'api_maker' : temp_record.maker_name,
                'api_volume' : temp_record.capacity,
                'api_list_price' : temp_record.tanka,
            }
            existing_product.product_tmpl_id.write(template_vals)
            
            # Update product variant specific fields
            product_vals = {
                'default_code': temp_record.item_sku,
            }
            existing_product.write(product_vals)
            
            _logger.info(f"Updated product: {existing_product.name} (SKU: {temp_record.item_sku})")
            return existing_product
        else:
            # Create new product template with variant
            template_vals = {
                'name': temp_record.item_name or 'Unknown Product',
                'list_price': temp_record.teika_tanka or 0.0,
                'standard_price': temp_record.tanka or 0.0,  # Cost price
                'type': 'consu',  # Consumable product
                'sale_ok': True,
                'purchase_ok': True,
                'default_code': temp_record.item_sku,  # This will be inherited by the variant
                'api_sku' : temp_record.item_sku,
                'api_supplier_sku' : temp_record.supp_sku,
                'api_maker' : temp_record.maker_name,
                'api_volume' : temp_record.capacity,
                'api_list_price' : temp_record.tanka,
            }
            
            # Create template (this automatically creates a product.product variant)
            new_template = ProductTemplate.create(template_vals)
            
            # Get the automatically created product variant
            new_product = new_template.product_variant_id
            
            # Ensure the default_code is set on the variant
            if new_product and temp_record.item_sku:
                new_product.default_code = temp_record.item_sku
            
            _logger.info(f"Created new product: {new_template.name} (SKU: {temp_record.item_sku})")
            return new_product
    
    def _create_sale_order(self, first_record, line_data):
        """Create sale.order with order lines"""
        SaleOrder = self.env['sale.order']
        ResPartner = self.env['res.partner']
        ResCompany = self.env['res.company']
        
        try:
            # Find partner by dealer_customer_cd
            partner = None
            if first_record.dealer_customer_cd:
                partner = ResPartner.search([('ref', '=', first_record.dealer_customer_cd)], limit=1)
            
            # If partner not found, try to find by email or create a new one
            if not partner and first_record.customer_email:
                partner = ResPartner.search([('email', '=', first_record.customer_email)], limit=1)
            
            if not partner:
                # Create a new partner if not found
                partner_vals = {
                    'name': first_record.customer_kikanname or first_record.customer_tanto or 'Unknown Customer',
                    'email': first_record.customer_email,
                    'ref': first_record.dealer_customer_cd,
                    'customer_rank': 1,
                }
                partner = ResPartner.create(partner_vals)
                _logger.info(f"Created new partner: {partner.name}")
            
            # Find company by x_external_company_cod
            company = None
            if first_record.dealer_co_cd:
                company = ResCompany.search([('x_external_company_cod', '=', first_record.dealer_co_cd)], limit=1)
            
            if not company:
                company = self.env.company  # Use default company if not found
            
            # Get the earliest order date from all selected items
            order_dates = [ld['temp_record'].order_date for ld in line_data if ld['temp_record'].order_date]
            earliest_date = min(order_dates) if order_dates else fields.Datetime.now()
            
            # Collect all delivery dates and comments for the notes
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
                    'sku' : temp_rec.item_sku,
                    'supplier_sku' : temp_rec.supp_sku,
                    'maker' : temp_rec.maker_name,
                    'volume' : temp_rec.capacity,
                    'list_price' : temp_rec.tanka,
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
