# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Custom fields for DOG integration
    export_to_dog = fields.Boolean(
        string='Exported to DOG',
        default=False,
        readonly=True,
        copy=False,
        help='Indicates if this purchase order has been exported to DOG system'
    )
    dog_export_date = fields.Datetime(
        string='DOG Export Date',
        readonly=True,
        copy=False,
        help='Date and time when this order was exported to DOG'
    )
    dog_export_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='DOG Export Status', default='pending', readonly=True, copy=False)
    dog_export_message = fields.Text(
        string='DOG Export Message',
        readonly=True,
        copy=False,
        help='Response or error message from DOG API'
    )
    x_delivery_mode = fields.Selection([
        ('company', 'Company Delivery'),
        ('customer_drop_ship', 'Direct Shipment to Customer')
    ], string='Delivery Mode', default='company', required=True,
       help='1=自社、2=直送 (Company or Direct Ship)')
    x_ship_to_partner_id = fields.Many2one(
        'res.partner',
        string='Ship to Partner',
        help='Delivery destination partner (for direct shipment)'
    )

    # DOG API Configuration
    DOG_API_URL = "https://stage.scm-bio.net/api/odoo/create/index.php"
    DOG_API_USERNAME = "odoo"
    DOG_API_PASSWORD = "oaJE2@5V"

    def button_confirm(self):
        """Override to send data to DOG API after confirmation"""
        res = super(PurchaseOrder, self).button_confirm()
        
        # Send to DOG API after confirmation
        for order in self:
            if not order.export_to_dog:
                try:
                    order.send_to_dog_api()
                except Exception as e:
                    _logger.error(f"Failed to send PO {order.name} to DOG API: {str(e)}")
                    # Don't block the confirmation, just log the error
                    order.write({
                        'dog_export_status': 'failed',
                        'dog_export_message': str(e)
                    })
        
        return res

    def action_send_to_dog_manual(self):
        """Manual button to resend to DOG API"""
        self.ensure_one()
        if self.state not in ['purchase', 'done']:
            raise UserError(_('Only confirmed purchase orders can be sent to DOG API.'))
        
        return self.send_to_dog_api()

    def send_to_dog_api(self):
        """Main method to prepare data and send to DOG API"""
        self.ensure_one()
        
        try:
            # Prepare data for all order lines
            api_data = self._prepare_dog_api_data()
            
            if not api_data:
                raise UserError(_('No data to send to DOG API. Please add order lines.'))
            
            # Send to API
            response = self._call_dog_api(api_data)
            
            # Update order status
            self.write({
                'export_to_dog': True,
                'dog_export_date': fields.Datetime.now(),
                'dog_export_status': 'success',
                'dog_export_message': f'Successfully sent {len(api_data)} line(s) to DOG API. Response: {response}'
            })
            
            _logger.info(f"Successfully sent PO {self.name} to DOG API")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Purchase Order successfully sent to DOG API.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except UserError as e:
            # Re-raise UserError as is (already formatted)
            error_msg = str(e)
            _logger.error(f"Error sending PO {self.name} to DOG API: {error_msg}")
            
            self.write({
                'dog_export_status': 'failed',
                'dog_export_message': error_msg
            })
            
            raise
            
        except Exception as e:
            # Format other exceptions into user-friendly messages
            error_msg = str(e)
            
            # Clean up technical error messages
            if 'Invalid language code' in error_msg:
                error_msg = _('Language configuration error. Please check system languages in Settings > Translations > Languages.')
            elif 'Connection' in error_msg or 'timeout' in error_msg.lower():
                error_msg = _('Cannot connect to DOG API. Please check your internet connection.')
            elif 'Authentication' in error_msg or '401' in error_msg:
                error_msg = _('Authentication failed. Please check API credentials.')
            
            _logger.error(f"Error sending PO {self.name} to DOG API: {str(e)}")
            
            self.write({
                'dog_export_status': 'failed',
                'dog_export_message': error_msg
            })
            
            raise UserError(_('Failed to send to DOG API: %s') % error_msg)

    def _prepare_dog_api_data(self):
        """Prepare data according to DOG API specification"""
        self.ensure_one()
        
        data_list = []
        sequence_num = 1
        
        for line in self.order_line:
            # Get ship-to partner (for direct shipment)
            ship_to_partner = self._get_ship_to_partner()
            
            # Determine delivery destination type
            delivery_type = '2' if self.x_delivery_mode == 'customer_drop_ship' else '1'
            
            # Get buyer (company) information
            buyer_partner = self.company_id.partner_id
            
            # Prepare line data according to specification
            line_data = {
                # 3. po_number - 発注番号
                'po_number': self.name or '',
                
                # 4. po_line_number - 発注明細行番号
                'po_line_number': line.sequence if line.sequence else sequence_num,
                
                # 5. order_date - 発注日 (YYYY-MM-DD format)
                'order_date': self.date_order.strftime('%Y-%m-%d') if self.date_order else '',
                
                # 6. requested_date - 納期（希望納期）
                'requested_date': line.date_planned.strftime('%Y-%m-%d') if line.date_planned else '',
                
                # 7. buyer_code - 発注元企業コード
                'buyer_code': buyer_partner.ref or '',
                
                # 8. buyer_name - 発注元企業名
                'buyer_name': self.company_id.name or '',
                
                # 9. supplier_code - 仕入先コード
                'supplier_code': self.partner_id.ref or '',
                
                # 10. supplier_name - 仕入先名
                'supplier_name': self.partner_id.name or '',
                
                # 11. supplier_quote_number - 見積番号（仕入先指定）
                'supplier_quote_number': self.partner_ref or '',
                
                # 12. delivery_destination_type - 納品区分 (1=自社、2=直送)
                'delivery_destination_type': delivery_type,
                
                # 13. ship_to_party_code - 納品先取引先コード
                'ship_to_party_code': ship_to_partner.ref or '',
                
                # 14. ship_to_party_name - 納品先取引先名
                'ship_to_party_name': ship_to_partner.name or '',
                
                # 15. ship_to_zip - 納品先郵便番号
                'ship_to_zip': ship_to_partner.zip or '',
                
                # 16. ship_to_state - 納品先都道府県
                'ship_to_state': ship_to_partner.state_id.name if ship_to_partner.state_id else '',
                
                # 17. ship_to_city - 納品先市区町村
                'ship_to_city': ship_to_partner.city or '',
                
                # 18. ship_to_street - 納品先番地・建物名
                'ship_to_street': self._get_full_street(ship_to_partner),
                
                # 19. ship_to_phone - 納品先電話番号
                'ship_to_phone': ship_to_partner.phone or '',
                
                # 20. item_code - 商品コード
                'item_code': line.product_id.default_code or '',
                
                # 21. item_name - 商品名
                'item_name': self._get_product_name_japanese(line.product_id),
                
                # 22. ordered_qty - 発注数量
                'ordered_qty': float(line.product_qty or 0),
                
                # 23. unit_price - 単価（税抜）
                'unit_price': float(line.price_unit or 0),
                
                # 24. line_amount - 金額（税抜・行小計）
                'line_amount': float(line.price_subtotal or 0),
                
                # 25. po_remark - 備考（ヘッダ）
                'po_remark': self.notes or '',
                
                # 26. line_remark - 備考（明細）
                'line_remark': line.name or '',  # Using line description as remark
            }
            
            data_list.append(line_data)
            sequence_num += 1
        
        return data_list

    def _get_ship_to_partner(self):
        """Get the ship-to partner based on delivery mode"""
        self.ensure_one()
        
        if self.x_delivery_mode == 'customer_drop_ship' and self.x_ship_to_partner_id:
            return self.x_ship_to_partner_id
        elif self.dest_address_id:
            return self.dest_address_id
        else:
            # Default to company partner
            return self.company_id.partner_id

    def _get_full_street(self, partner):
        """Combine street and street2 for full address"""
        if not partner:
            return ''
        
        street_parts = []
        if partner.street:
            street_parts.append(partner.street)
        if partner.street2:
            street_parts.append(partner.street2)
        
        return ' '.join(street_parts)

    def _get_product_language_code(self):
        """Get the appropriate language code for product names"""
        # Priority:
        # 1. Japanese if available
        # 2. Current user's language
        # 3. System default language
        
        # Try Japanese first (as per specification)
        lang_codes = ['ja_JP', self.env.user.lang, self.env.lang]
        
        for code in lang_codes:
            if code:
                lang = self.env['res.lang'].search([('code', '=', code), ('active', '=', True)], limit=1)
                if lang:
                    return code
        
        # Fallback to English or first available language
        return 'en_US'

    def _get_product_name_japanese(self, product):
        """Get product name in Japanese if available, fallback to default"""
        if not product:
            return ''
        
        try:
            # Get appropriate language code
            lang_code = self._get_product_language_code()
            
            # Get product name with the language context
            product_with_lang = product.with_context(lang=lang_code)
            return product_with_lang.display_name or product.name or ''
                
        except Exception as e:
            # If any error, just return the default product name
            _logger.warning(f"Could not get translated product name: {str(e)}")
            return product.display_name or product.name or ''

    def _call_dog_api(self, data_list):
        """Make the actual API call to DOG system"""
        
        url = self.DOG_API_URL
        
        # Use ensure_ascii=True to properly encode Japanese characters
        # This converts Unicode to \uXXXX format which is safer for the API
        payload = json.dumps({
            "data": data_list
        }, ensure_ascii=True)
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Basic b2RvbzpvYUpFMkA1Vg=='  # Base64 encoded "odoo:oaJE2@5V"
        }
        
        try:
            _logger.info(f"Sending request to DOG API: {url}")
            _logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                url,
                headers=headers,
                data=payload.encode('utf-8'),
                timeout=30
            )
            
            _logger.info(f"DOG API Response Status: {response.status_code}")
            _logger.debug(f"DOG API Response: {response.text}")
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                raise UserError(f"Invalid JSON response from API: {response.text}")
            
            # Check API-level success
            success = response_data.get('success', False)
            inserted = response_data.get('inserted', 0)
            failed = response_data.get('failed', 0)
            errors = response_data.get('errors', [])
            
            # Log the results
            _logger.info(f"DOG API Results - Inserted: {inserted}, Failed: {failed}")
            
            if errors:
                _logger.error(f"DOG API Errors: {errors}")
            
            # Check if data was actually inserted
            if not success or inserted == 0 or failed > 0:
                # Build error message
                error_msg = "Failed to insert data into DOG system.\n"
                
                if errors:
                    error_msg += "API Errors:\n"
                    for idx, error in enumerate(errors, 1):
                        # Clean up error message
                        clean_error = error.replace('\\n', '\n').replace('\\t', '\t')
                        
                        # Check for specific encoding errors
                        if 'SJIS' in error or 'invalid byte sequence' in error:
                            clean_error += "\n   → This is a character encoding issue. Japanese characters may not be properly supported by the DOG database."
                        
                        error_msg += f"{idx}. {clean_error}\n"
                else:
                    error_msg += f"Inserted: {inserted}, Failed: {failed}"
                
                raise UserError(error_msg)
            
            # Success - return response summary
            return f"Successfully inserted {inserted} record(s). Response: {response.text}"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API Request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - Response: {e.response.text}"
            raise UserError(error_msg)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # You can add custom fields for line-level remarks if needed
    x_line_remark = fields.Char(
        string='Line Remark',
        help='Specific remark for this order line'
    )
