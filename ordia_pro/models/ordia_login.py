# ========================================
# FILE: ordia/models/ordia_login.py
# ========================================
import requests
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)

class OrdiaLogin(models.Model):
    _name = 'ordia.login'
    _description = 'ORDIA Login Token Storage'

    username = fields.Char(string='Username', required=True)
    password = fields.Char(string='Password')
    token = fields.Char(string='API Token')
    token_expiry = fields.Datetime(string='Token Expiry Time')
    dealer_co_cd = fields.Char(string='Dealer Code')
    user_name = fields.Char(string='User Name')
    user_email = fields.Char(string='User Email')
    last_login = fields.Datetime(string='Last Login', default=fields.Datetime.now)
    
    @api.model
    def check_valid_token(self):
        """Check if current user has a valid token"""
        current_user = self.env.user
        
        # Search for existing login record for this user
        login_record = self.search([
            ('create_uid', '=', current_user.id)
        ], limit=1, order='last_login desc')
        
        if login_record and login_record.token and login_record.token_expiry:
            # Check if token is still valid (within 3 hours)
            now = fields.Datetime.now()
            if login_record.token_expiry > now:
                _logger.info(f"Valid token found for user {current_user.name}")
                return {
                    'has_valid_token': True,
                    'token': login_record.token,
                    'dealer_co_cd': login_record.dealer_co_cd,
                    'user_name': login_record.user_name,
                    'user_email': login_record.user_email,
                    'login_id': login_record.id,
                }
            else:
                _logger.info(f"Token expired for user {current_user.name}")
        
        return {'has_valid_token': False}
    
    @api.model
    def action_open_ordia(self):
        """Main entry point - check token and redirect accordingly"""
        token_check = self.check_valid_token()
        
        if token_check['has_valid_token']:
            # Token is valid, go directly to cart search
            search_wizard = self.env['ordia.cart.search'].create({
                'token': token_check['token'],
                'dealer_co_cd': token_check['dealer_co_cd'],
            })
            
            context = {
                'default_token': token_check['token'],
                'default_dealer_co_cd': token_check['dealer_co_cd'],
                'default_user_name': token_check['user_name'],
                'default_user_email': token_check['user_email'],
            }
            
            return {
                'name': 'ORDIA Cart Search',
                'type': 'ir.actions.act_window',
                'res_model': 'ordia.cart.search',
                'res_id': search_wizard.id,
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
        else:
            # No valid token, show login form
            return {
                'name': 'ORDIA Login',
                'type': 'ir.actions.act_window',
                'res_model': 'ordia.login',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_username': ''},
            }
    
    def action_login(self):
        """Authenticate with ORDIA API, fetch nonyu data, and redirect to cart list"""
        self.ensure_one()
        
        # Step 1: Authenticate
        url = "https://ordia-api.bio-purchase.com/api/ec-users/authenticate"
        payload = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30, verify=False)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('http') == 200 and result.get('token'):
                token = result['token']
                user_info = result.get('userInfo', {})
                
                # Get dealer_co_cd from company settings instead of API response
                company = self.env.company
                dealer_co_cd = company.x_external_company_cod if hasattr(company, 'x_external_company_cod') else ''
                
                if not dealer_co_cd:
                    raise UserError('Company external code (dealer_co_cd) is not configured. Please set x_external_company_code in Company settings.')
                
                # Step 2: Fetch nonyu data
                self._fetch_and_save_nonyu_data(token, dealer_co_cd)
                
                # Step 3: Save/Update token with 3 hours expiry
                token_expiry = fields.Datetime.now() + timedelta(hours=3)
                current_user = self.env.user
                
                # Check if login record already exists for this user
                existing_login = self.search([
                    ('create_uid', '=', current_user.id)
                ], limit=1, order='last_login desc')
                
                login_vals = {
                    'username': self.username,
                    'password': self.password,  # In production, consider encrypting this
                    'token': token,
                    'token_expiry': token_expiry,
                    'dealer_co_cd': dealer_co_cd,
                    'user_name': user_info.get('name', ''),
                    'user_email': user_info.get('email', ''),
                    'last_login': fields.Datetime.now(),
                }
                
                if existing_login:
                    # Update existing record
                    existing_login.write(login_vals)
                    _logger.info(f"Updated token for user: {current_user.name}")
                else:
                    # Create new record
                    self.create(login_vals)
                    _logger.info(f"Created new token record for user: {current_user.name}")
                
                # Store token and user info in context
                context = {
                    'default_token': token,
                    'default_dealer_co_cd': dealer_co_cd,
                    'default_user_name': user_info.get('name', ''),
                    'default_user_email': user_info.get('email', ''),
                }
                
                # Create initial search wizard with token
                search_wizard = self.env['ordia.cart.search'].create({
                    'token': token,
                    'dealer_co_cd': dealer_co_cd,
                })
                
                # Return action to open cart search
                return {
                    'name': 'ORDIA Cart Search',
                    'type': 'ir.actions.act_window',
                    'res_model': 'ordia.cart.search',
                    'res_id': search_wizard.id,
                    'view_mode': 'form',
                    'target': 'new',
                    'context': context,
                }
            else:
                raise UserError('Login failed: Invalid credentials')
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"ORDIA API Error: {str(e)}")
            raise UserError(f'Connection error: {str(e)}')
        except Exception as e:
            _logger.error(f"Login Error: {str(e)}")
            raise UserError(f'Login failed: {str(e)}')
    
    def _fetch_and_save_nonyu_data(self, token, dealer_co_cd):
        """Fetch nonyu data from API and save to res.partner"""
        
        # Build URL with parameters
        url = "https://ordia-api.bio-purchase.com/ordia/v1.0/nonyu-lists"
        params = {
            'token': token,
            'dealer_co_cd': dealer_co_cd
        }
        
        try:
            response = requests.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('http') == 200:
                data_list = result.get('dataList', [])
                
                for nonyu_data in data_list:
                    self._create_or_update_partner(nonyu_data)
                
                _logger.info(f"Successfully synced {len(data_list)} nonyu records")
                
                # Show notification to user
                if data_list:
                    message = f"Successfully synced {len(data_list)} delivery addresses from ORDIA"
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Sync Complete',
                            'message': message,
                            'type': 'success',
                            'sticky': False,
                        }
                    }
            else:
                _logger.warning(f"Nonyu API returned status: {result.get('http')}, message: {result.get('message')}")
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"Nonyu API Error: {str(e)}")
            # Don't raise error here, just log it - we still want login to succeed
        except Exception as e:
            _logger.error(f"Nonyu Data Processing Error: {str(e)}")
            # Don't raise error here, just log it - we still want login to succeed
    
    def _create_or_update_partner(self, nonyu_data):
        """Create or update res.partner record from nonyu data"""
        
        ResPartner = self.env['res.partner']
        
        # Prepare partner values
        partner_vals = {
            'name': nonyu_data.get('nonyu_name', ''),
            'company_type': 'company',
            'ref': nonyu_data.get('nonyu_code', ''),
            'type': 'delivery',
            'street': nonyu_data.get('nonyu_address', ''),
            'zip': nonyu_data.get('nonyu_zip', ''),
            'active': nonyu_data.get('is_active', '1') == '1',
            'is_company': True,
        }
        
        # Handle email - check different possible fields
        email = None
        if nonyu_data.get('nonyu_email_dealer'):
            email = nonyu_data.get('nonyu_email_dealer')
        elif nonyu_data.get('emails') and isinstance(nonyu_data['emails'], list) and nonyu_data['emails']:
            # If emails is a list, take the first one
            email = nonyu_data['emails'][0]
        
        if email:
            partner_vals['email'] = email
        
        # Handle parent partner if parent_nonyu_code exists
        parent_nonyu_code = nonyu_data.get('parent_nonyu_code')
        if parent_nonyu_code:
            parent_partner = ResPartner.search([('ref', '=', parent_nonyu_code)], limit=1)
            if parent_partner:
                partner_vals['parent_id'] = parent_partner.id
        
        # Check if partner already exists
        nonyu_code = nonyu_data.get('nonyu_code')
        if nonyu_code:
            existing_partner = ResPartner.search([('ref', '=', nonyu_code)], limit=1)
            
            if existing_partner:
                # Update existing partner
                existing_partner.write(partner_vals)
                _logger.info(f"Updated partner: {existing_partner.name} (ref: {nonyu_code})")
            else:
                # Create new partner
                new_partner = ResPartner.create(partner_vals)
                _logger.info(f"Created new partner: {new_partner.name} (ref: {nonyu_code})")
        else:
            _logger.warning(f"Skipping nonyu record without nonyu_code: {nonyu_data}")