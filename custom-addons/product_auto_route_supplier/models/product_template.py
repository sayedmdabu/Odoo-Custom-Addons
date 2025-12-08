# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # External API fields from specification
    api_sku = fields.Char(
        string='API SKU',
        index=True,
        help='Product SKU from external system (get_product_ec.sku)'
    )
    
    api_supplier_sku = fields.Char(
        string='Supplier SKU',
        help='Supplier-specific SKU (get_product_ec.supplier_sku)'
    )
    
    api_price_group = fields.Char(
        string='Price Group',
        index=True,
        help='Price group for rate determination (get_product_ec.price_group)'
    )
    
    api_maker = fields.Char(
        string='Manufacturer',
        index=True,
        help='Manufacturer name (get_product_ec.maker_name)'
    )
    
    api_supplier_comp_code = fields.Char(
        string='Supplier Company Code',
        index=True,
        help='External supplier company code (get_product_ec.supplier_comp_code)'
    )
    
    api_supplier_comp_name = fields.Char(
        string='Supplier Company Name',
        help='Supplier company name from API'
    )
    
    api_sales_origin_maker_name = fields.Char(
        string='Origin Maker Name',
        help='Original manufacturer name (get_product_ec.sales_origin_maker_name)'
    )
    
    api_volume = fields.Char(
        string='API Volume',
        help='Volume from external system'
    )
    
    api_list_price = fields.Float(
        string='API List Price',
        digits='Product Price',
        help='List price from external system (get_product_ec.list_price)'
    )
    
    purchase_price_fixed = fields.Float(
        string='Fixed Purchase Price',
        digits='Product Price',
        help='Fixed purchase price per SKU (highest priority in calculation)'
    )
    
    # Status fields
    auto_process_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Auto Process Status', default='pending', readonly=True)
    
    auto_process_message = fields.Text(
        string='Auto Process Message',
        readonly=True
    )

    @api.onchange('api_sku')
    def _onchange_api_sku(self):
        """
        Auto-extract supplier code from SKU if it follows pattern.
        Pattern: SKU often starts with supplier code (e.g., "20000109-...")
        """
        if self.api_sku and not self.api_supplier_comp_code:
            # Try to extract supplier code from SKU
            # Pattern 1: "20000109-..." or "20000109..." (8 digits at start)
            match = re.match(r'^(\d{8})', self.api_sku)
            if match:
                supplier_code = match.group(1)
                self.api_supplier_comp_code = supplier_code
                _logger.info(
                    f"Auto-extracted supplier code '{supplier_code}' from SKU '{self.api_sku}'"
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-extract supplier code and trigger auto-processing"""
        # Auto-extract supplier code from SKU before creating
        for vals in vals_list:
            if vals.get('api_sku') and not vals.get('api_supplier_comp_code'):
                sku = vals['api_sku']
                match = re.match(r'^(\d{8})', sku)
                if match:
                    vals['api_supplier_comp_code'] = match.group(1)
                    _logger.info(
                        f"Auto-extracted supplier code '{vals['api_supplier_comp_code']}' "
                        f"from SKU '{sku}'"
                    )
        
        records = super(ProductTemplate, self).create(vals_list)
        
        for record in records:
            record.auto_process_status = 'pending'
            try:
                record._auto_process_product()
            except Exception as e:
                _logger.error(
                    f"Error auto-processing product {record.id}: {str(e)}",
                    exc_info=True
                )
                record.auto_process_status = 'error'
                record.auto_process_message = str(e)
        
        return records

    def write(self, vals):
        """Override write to trigger auto-processing if relevant fields change"""
        result = super(ProductTemplate, self).write(vals)
        
        # Check if any relevant field was updated
        relevant_fields = [
            'api_sku', 'api_supplier_comp_code', 'api_price_group',
            'api_maker', 'api_list_price', 'purchase_price_fixed'
        ]
        
        if any(field in vals for field in relevant_fields):
            for record in self:
                try:
                    record._auto_process_product()
                except Exception as e:
                    _logger.error(
                        f"Error auto-processing product {record.id}: {str(e)}",
                        exc_info=True
                    )
                    record.auto_process_status = 'error'
                    record.auto_process_message = str(e)
        
        return result

    def action_extract_supplier_code(self):
        """
        Manual action to extract supplier code from SKU for selected products
        """
        extracted_count = 0
        for record in self:
            if record.api_sku and not record.api_supplier_comp_code:
                match = re.match(r'^(\d{8})', record.api_sku)
                if match:
                    record.api_supplier_comp_code = match.group(1)
                    extracted_count += 1
                    _logger.info(
                        f"Extracted supplier code '{record.api_supplier_comp_code}' "
                        f"from SKU '{record.api_sku}' for product {record.name}"
                    )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Extracted supplier code for %d product(s)') % extracted_count,
                'type': 'success' if extracted_count > 0 else 'warning',
                'sticky': False,
            }
        }

    def _auto_process_product(self):
        """
        Main orchestration method for automatic product processing
        Steps:
        1. Assign Buy route
        2. Assign MTO route (OCA stock_route_mto)
        3. Identify vendor from external code
        4. Calculate purchase price
        5. Upsert product.supplierinfo
        """
        self.ensure_one()
        
        _logger.info(f"=== Auto-processing product: {self.name} (ID: {self.id}) ===")
        
        try:
            self.auto_process_status = 'processing'
            messages = []
            
            # Step 1 & 2: Assign routes
            route_msg = self._assign_routes()
            if route_msg:
                messages.append(route_msg)
            
            # Step 3: Identify vendor
            vendor = self._identify_vendor()
            
            if not vendor:
                msg = (
                    f"Vendor not identified for supplier code: {self.api_supplier_comp_code}. "
                    f"Skipping supplierinfo creation."
                )
                _logger.warning(f"Product {self.name}: {msg}")
                messages.append(msg)
                self.auto_process_status = 'success'
                self.auto_process_message = '\n'.join(messages)
                return
            
            messages.append(f"Vendor identified: {vendor.name}")
            
            # Step 4: Calculate purchase price
            purchase_price = self._calculate_purchase_price()
            
            if not purchase_price:
                _logger.warning(
                    f"Product {self.name}: Purchase price could not be calculated. "
                    f"Using fallback."
                )
                purchase_price = self.api_list_price or self.list_price or 0.0
                messages.append(f"Using fallback purchase price: {purchase_price}")
            else:
                messages.append(f"Calculated purchase price: {purchase_price}")
            
            # Step 5: Upsert supplierinfo
            supplierinfo_msg = self._upsert_supplierinfo(vendor, purchase_price)
            if supplierinfo_msg:
                messages.append(supplierinfo_msg)
            
            self.auto_process_status = 'success'
            self.auto_process_message = '\n'.join(messages)
            
            _logger.info(
                f"=== Completed auto-processing for product: {self.name} ==="
            )
            
        except Exception as e:
            _logger.error(
                f"Error in _auto_process_product for {self.name}: {str(e)}",
                exc_info=True
            )
            self.auto_process_status = 'error'
            self.auto_process_message = f"Error: {str(e)}"
            raise

    def _assign_routes(self):
        """Assign Buy and MTO routes to product"""
        self.ensure_one()
        
        messages = []
        
        try:
            routes_to_add = []
            
            # Get Buy route - try multiple possible XML IDs
            buy_route = None
            buy_route_refs = [
                'purchase_stock.route_warehouse0_buy',
                'stock.route_warehouse0_buy',
            ]
            
            for ref in buy_route_refs:
                try:
                    buy_route = self.env.ref(ref, raise_if_not_found=False)
                    if buy_route:
                        _logger.debug(f"Found Buy route with XML ID: {ref}")
                        break
                except:
                    continue
            
            # If XML ID approach fails, search by name
            if not buy_route:
                buy_route = self.env['stock.route'].search([
                    ('name', 'ilike', 'buy')
                ], limit=1)
            
            if buy_route:
                if buy_route not in self.route_ids:
                    routes_to_add.append(buy_route.id)
                    messages.append(f"Adding Buy route")
                    _logger.info(f"Adding Buy route to product {self.name}")
                else:
                    _logger.debug(f"Buy route already assigned to {self.name}")
            else:
                msg = "Warning: Buy route not found"
                messages.append(msg)
                _logger.warning(msg)
            
            # Get MTO route from OCA module
            mto_route = None
            mto_route_refs = [
                'stock_route_mto.route_mto',
                'stock_mts_mto_rule.route_mto',
            ]
            
            for ref in mto_route_refs:
                try:
                    mto_route = self.env.ref(ref, raise_if_not_found=False)
                    if mto_route:
                        _logger.debug(f"Found MTO route with XML ID: {ref}")
                        break
                except:
                    continue
            
            # If XML ID approach fails, search by name
            if not mto_route:
                mto_route = self.env['stock.route'].search([
                    '|',
                    ('name', 'ilike', 'make to order'),
                    ('name', 'ilike', 'mto')
                ], limit=1)
            
            if mto_route:
                if mto_route not in self.route_ids:
                    routes_to_add.append(mto_route.id)
                    messages.append(f"Adding MTO route")
                    _logger.info(f"Adding MTO route to product {self.name}")
                else:
                    _logger.debug(f"MTO route already assigned to {self.name}")
            else:
                msg = "Warning: MTO route not found. Install OCA stock_route_mto module."
                messages.append(msg)
                _logger.warning(msg)
            
            if routes_to_add:
                # Use (4, id) to add without removing existing routes
                self.write({
                    'route_ids': [(4, route_id) for route_id in routes_to_add]
                })
            else:
                _logger.debug(f"No new routes to add for product {self.name}")
            
            return '\n'.join(messages) if messages else None
            
        except Exception as e:
            error_msg = f"Error assigning routes: {str(e)}"
            _logger.error(
                f"Error assigning routes to product {self.name}: {str(e)}",
                exc_info=True
            )
            return error_msg

    def _identify_vendor(self):
        """
        Identify vendor using external code mapping
        
        Returns:
            res.partner record or False
        """
        self.ensure_one()
        
        if not self.api_supplier_comp_code:
            _logger.debug(
                f"Product {self.name}: No api_supplier_comp_code set. "
                f"Cannot identify vendor."
            )
            return False
        
        # Use supplier.external.mapping to find vendor
        mapping_model = self.env['supplier.external.mapping']
        vendor = mapping_model.get_vendor_from_external_code(
            self.api_supplier_comp_code
        )
        
        return vendor

    def _calculate_purchase_price(self):
        """
        Calculate purchase price with priority logic:
        1. Fixed Purchase Price (purchase_price_fixed)
        2. Price Group Rate (list_price * group_rate)
        3. Manufacturer Rate (list_price * maker_rate)
        4. Fallback (list_price * 1.0)
        
        Returns:
            float: calculated price
        """
        self.ensure_one()
        
        # Priority 1: Fixed Purchase Price
        if self.purchase_price_fixed and self.purchase_price_fixed > 0:
            _logger.info(
                f"Product {self.name}: Using fixed purchase price: "
                f"{self.purchase_price_fixed}"
            )
            return self.purchase_price_fixed
        
        # Get list price (prefer api_list_price, fallback to list_price)
        list_price = self.api_list_price or self.list_price
        
        if not list_price or list_price <= 0:
            _logger.warning(
                f"Product {self.name}: No valid list price available for calculation"
            )
            return 0.0
        
        # Priority 2: Price Group Rate
        if self.api_supplier_comp_code and self.api_price_group:
            price_group_rate_model = self.env['price.group.rate']
            group_rate = price_group_rate_model.get_rate(
                self.api_supplier_comp_code,
                self.api_price_group
            )
            
            if group_rate:
                calculated_price = list_price * group_rate
                _logger.info(
                    f"Product {self.name}: Using price group rate: "
                    f"{list_price} × {group_rate} = {calculated_price}"
                )
                return calculated_price
        
        # Priority 3: Manufacturer Rate
        if self.api_supplier_comp_code and self.api_maker:
            maker_rate_model = self.env['maker.rate']
            maker_rate = maker_rate_model.get_rate(
                self.api_supplier_comp_code,
                self.api_maker
            )
            
            if maker_rate:
                calculated_price = list_price * maker_rate
                _logger.info(
                    f"Product {self.name}: Using manufacturer rate: "
                    f"{list_price} × {maker_rate} = {calculated_price}"
                )
                return calculated_price
        
        # Priority 4: Fallback
        _logger.info(
            f"Product {self.name}: Using fallback price (list_price × 1.0): "
            f"{list_price}"
        )
        return list_price

    def _upsert_supplierinfo(self, vendor, purchase_price):
        """
        Create or update product.supplierinfo
        
        Args:
            vendor: res.partner record
            purchase_price: calculated purchase price
            
        Returns:
            str: message describing the action taken
        """
        self.ensure_one()
        
        if not vendor:
            return None
        
        supplierinfo_model = self.env['product.supplierinfo']
        
        # Search for existing supplierinfo
        existing = supplierinfo_model.search([
            ('product_tmpl_id', '=', self.id),
            ('partner_id', '=', vendor.id),
        ], limit=1)
        
        vals = {
            'partner_id': vendor.id,
            'product_tmpl_id': self.id,
            'price': purchase_price,
            'currency_id': self.env.company.currency_id.id,
        }
        
        # Add product code if available
        if self.api_supplier_sku:
            vals['product_code'] = self.api_supplier_sku
        
        # Add product name if available
        if self.api_supplier_comp_name:
            vals['product_name'] = self.api_supplier_comp_name
        
        if existing:
            # Update existing
            existing.write(vals)
            msg = (
                f"Updated supplierinfo: vendor={vendor.name}, "
                f"price={purchase_price}"
            )
            _logger.info(
                f"Updated supplierinfo for product {self.name}, "
                f"vendor {vendor.name}, price {purchase_price}"
            )
        else:
            # Create new
            supplierinfo_model.create(vals)
            msg = (
                f"Created supplierinfo: vendor={vendor.name}, "
                f"price={purchase_price}"
            )
            _logger.info(
                f"Created supplierinfo for product {self.name}, "
                f"vendor {vendor.name}, price {purchase_price}"
            )
        
        return msg

    def action_reprocess_product(self):
        """Manual action to reprocess product"""
        for record in self:
            try:
                record._auto_process_product()
            except Exception as e:
                raise UserError(_(
                    f"Error reprocessing product {record.name}: {str(e)}"
                ))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d product(s) reprocessed successfully') % len(self),
                'type': 'success',
                'sticky': False,
            }
        }