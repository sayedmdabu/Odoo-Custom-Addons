# ========================================
# FILE: ordia/models/ordia_login.py
# ========================================
import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class OrdiaLogin(models.TransientModel):
    _name = 'ordia.login'
    _description = 'ORDIA Login'

    username = fields.Char(string='Username', required=True)
    password = fields.Char(string='Password', required=True)
    
    def action_login(self):
        """Authenticate with ORDIA API and redirect to cart list"""
        self.ensure_one()
        
        url = "https://api-staging.bio-purchase.com/api/ec-users/authenticate"
        payload = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('http') == 200 and result.get('token'):
                token = result['token']
                user_info = result.get('userInfo', {})
                kikan_code = user_info.get('kikan_code', '')
                
                # Store token and user info in context
                context = {
                    'default_token': token,
                    'default_dealer_co_cd': kikan_code,
                    'default_user_name': user_info.get('name', ''),
                    'default_user_email': user_info.get('email', ''),
                }
                
                # Create initial search wizard with token
                search_wizard = self.env['ordia.cart.search'].create({
                    'token': token,
                    'dealer_co_cd': kikan_code,
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