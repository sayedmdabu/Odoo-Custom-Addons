# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Shows discounted unit price beside normal unit price
    effective_unit_price = fields.Float(
        string="Discounted Unit Price",
        compute="_compute_effective_unit_price",
        store=True,
        digits="Product Price",
        help="Unit price after applying discount"
    )
    
    # Shows the discount amount (how much is saved)
    discount_amount = fields.Monetary(
        string="Discount Amount",
        compute="_compute_discount_amount",
        store=True,
        help="Amount saved due to discount"
    )

    applied_rate_source = fields.Selection([
        ('fixed', 'Fixed Purchase Price'),
        ('price_group', 'Price Group Rate'),
        ('maker', 'Manufacturer Rate'),
        ('manual', 'Manual'),
        ('none', 'No Discount'),
    ], string='Discount Source', readonly=True, copy=False)

    applied_rate_value = fields.Float(
        string='Applied Rate',
        digits=(5, 4),
        readonly=True,
        copy=False,
        help='The rate that was applied (if any)'
    )

    # ------------------------------------------------------
    # Onchange: apply discount automatically on product select
    # ------------------------------------------------------
    @api.onchange('product_id')
    def _onchange_product_id_apply_discount(self):
        """Apply discount when product is selected"""
        if not self.product_id or not self.product_template_id:
            return

        # Only apply if there is no manual discount
        if self.discount == 0.0:
            discount_info = self._calculate_sales_discount(self.product_template_id)

            if discount_info and discount_info.get('discount_percent', 0) > 0:
                self.discount = discount_info['discount_percent']
                self.applied_rate_source = discount_info['source']
                self.applied_rate_value = discount_info['rate_value']

    # ------------------------------------------------------
    # Compute effective discounted unit price
    # ------------------------------------------------------
    @api.depends('price_unit', 'discount')
    def _compute_effective_unit_price(self):
        """Calculate the price after discount"""
        for line in self:
            if line.discount:
                line.effective_unit_price = line.price_unit * (1 - line.discount / 100)
            else:
                line.effective_unit_price = line.price_unit

    # ------------------------------------------------------
    # Compute discount amount
    # ------------------------------------------------------
    @api.depends('price_unit', 'discount', 'product_uom_qty')
    def _compute_discount_amount(self):
        """Calculate total discount amount"""
        for line in self:
            if line.discount:
                discount_per_unit = line.price_unit * (line.discount / 100)
                line.discount_amount = discount_per_unit * line.product_uom_qty
            else:
                line.discount_amount = 0.0

    # ------------------------------------------------------
    # Override price_subtotal to use discounted price
    # ------------------------------------------------------
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Override amount calculation to properly handle discount.
        Amount = Discounted Unit Price × Quantity
        """
        for line in self:
            # Calculate price after discount
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            
            # Calculate taxes
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id
            )
            
            # Update amounts
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    # ------------------------------------------------------
    # Discount Logic - Match by Supplier Code ONLY
    # ------------------------------------------------------
    def _calculate_sales_discount(self, product_tmpl):
        """
        Calculate discount percentage based on supplier code match ONLY.
        
        Logic:
        1. Search Price Group Rate table by supplier_comp_code only
        2. Pick the best rate (lowest = highest discount)
        3. If not found, search Manufacturer Rate table by supplier_comp_code only
        4. Pick the best rate (lowest = highest discount)
        
        Returns:
            dict: discount info or False
        """
        # Check if product has supplier code
        if not product_tmpl.api_supplier_comp_code:
            return False

        supplier_code = product_tmpl.api_supplier_comp_code

        # Priority 1: Search Price Group Rate by supplier code ONLY
        price_group_rates = self.env['price.group.rate'].search([
            ('supplier_comp_code', '=', supplier_code),
            ('active', '=', True),
        ], order='rate asc')  # Lowest rate first = highest discount

        # Filter valid rates (not 1.0 and date valid)
        valid_price_rates = []
        from datetime import date
        today = date.today()
        
        for rate_record in price_group_rates:
            # Skip rate = 1.0 (no discount)
            if rate_record.rate == 1.0:
                continue
            
            # Check date validity
            if rate_record.valid_from and today < rate_record.valid_from:
                continue
            if rate_record.valid_to and today > rate_record.valid_to:
                continue
            
            valid_price_rates.append(rate_record)
        
        if valid_price_rates:
            # Use the first one (lowest rate = highest discount)
            best_rate = valid_price_rates[0]
            discount_percent = (1.0 - best_rate.rate) * 100.0
            
            _logger.info(
                f"Price Group discount: {supplier_code}/"
                f"{best_rate.group_name} = {discount_percent:.2f}%"
            )
            
            return {
                'discount_percent': discount_percent,
                'source': 'price_group',
                'rate_value': best_rate.rate,
            }

        # Priority 2: Search Manufacturer Rate by supplier code ONLY
        maker_rates = self.env['maker.rate'].search([
            ('supplier_comp_code', '=', supplier_code),
            ('active', '=', True),
        ], order='rate asc')  # Lowest rate first = highest discount

        # Filter valid rates (not 1.0 and date valid)
        valid_maker_rates = []
        
        for rate_record in maker_rates:
            # Skip rate = 1.0 (no discount)
            if rate_record.rate == 1.0:
                continue
            
            # Check date validity
            if rate_record.valid_from and today < rate_record.valid_from:
                continue
            if rate_record.valid_to and today > rate_record.valid_to:
                continue
            
            valid_maker_rates.append(rate_record)
        
        if valid_maker_rates:
            # Use the first one (lowest rate = highest discount)
            best_rate = valid_maker_rates[0]
            discount_percent = (1.0 - best_rate.rate) * 100.0
            
            _logger.info(
                f"Manufacturer discount: {supplier_code}/"
                f"{best_rate.maker_name} = {discount_percent:.2f}%"
            )
            
            return {
                'discount_percent': discount_percent,
                'source': 'maker',
                'rate_value': best_rate.rate,
            }

        # No discount found
        return False

    # ------------------------------------------------------
    # Apply discount on programmatic creation
    # ------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Apply discount when creating lines programmatically"""
        lines = super(SaleOrderLine, self).create(vals_list)

        for line in lines:
            if line.product_id and line.discount == 0.0 and not line.applied_rate_source:
                discount_info = line._calculate_sales_discount(line.product_template_id)
                
                if discount_info and discount_info.get('discount_percent', 0) > 0:
                    line.write({
                        'discount': discount_info['discount_percent'],
                        'applied_rate_source': discount_info['source'],
                        'applied_rate_value': discount_info['rate_value'],
                    })
                else:
                    line.write({
                        'applied_rate_source': 'none',
                        'applied_rate_value': 0.0,
                    })

        return lines

    # ------------------------------------------------------
    # Write override to track manual changes
    # ------------------------------------------------------
    def write(self, vals):
        """Track when discount is manually changed"""
        if 'discount' in vals and not self.env.context.get('skip_discount_tracking'):
            for line in self:
                if line.applied_rate_source in ['price_group', 'maker'] and \
                   vals['discount'] != line.discount:
                    vals['applied_rate_source'] = 'manual'
                    vals['applied_rate_value'] = 0.0

        return super(SaleOrderLine, self).write(vals)

    # ------------------------------------------------------
    # Manual reapply auto discount
    # ------------------------------------------------------
    def action_reapply_automatic_discount(self):
        """Manually trigger discount recalculation"""
        for line in self:
            if line.product_template_id:
                discount_info = line._calculate_sales_discount(line.product_template_id)
                
                if discount_info and discount_info.get('discount_percent', 0) > 0:
                    line.with_context(skip_discount_tracking=True).write({
                        'discount': discount_info['discount_percent'],
                        'applied_rate_source': discount_info['source'],
                        'applied_rate_value': discount_info['rate_value'],
                    })
                else:
                    line.with_context(skip_discount_tracking=True).write({
                        'discount': 0.0,
                        'applied_rate_source': 'none',
                        'applied_rate_value': 0.0,
                    })


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_reapply_all_discounts(self):
        """Reapply automatic discounts to all order lines"""
        self.ensure_one()
        if self.order_line:
            self.order_line.action_reapply_automatic_discount()