from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class TestApiController(http.Controller):

    @http.route('/api/test_post', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_test_post(self, **post):
        """
        POST API to create records in test_post_api table
        
        Endpoint: http://your-domain:port/api/test_post
        Method: POST
        Content-Type: application/json
        
        Request JSON:
        {
            "jsonrpc": "2.0",
            "params": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "note": "Test note"
            }
        }
        
        Or with fields filter:
        {
            "jsonrpc": "2.0",
            "params": {
                "fields": ["name","email","phone","note"],
                "values": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "1234567890",
                    "note": "Test note"
                }
            }
        }
        """
        try:
            _logger.info('POST API called with data: %s', post)
            
            # Handle two formats: direct values or fields+values structure
            if 'values' in post:
                fields_list = post.get("fields", [])
                values = post.get("values", {})
                
                # Keep only allowed fields from 'fields' list
                if fields_list:
                    data = {field: values.get(field) for field in fields_list if field in values}
                else:
                    data = values
            else:
                # Direct format - all params are field values
                data = post
            
            # Validate required fields
            if not data.get("name"):
                return {
                    "success": False,
                    "error": "Name is required",
                    "error_code": "MISSING_NAME"
                }
            
            # Filter only allowed fields
            allowed_fields = ['name', 'email', 'phone', 'note', 'active']
            filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            # Create record in database
            record = request.env['test.post.api'].sudo().create(filtered_data)
            
            _logger.info('Record created successfully with ID: %s', record.id)
            
            return {
                "success": True,
                "message": "Data saved successfully",
                "data": {
                    "id": record.id,
                    "name": record.name,
                    "email": record.email,
                    "phone": record.phone,
                    "note": record.note,
                    "created_date": record.create_date.strftime('%Y-%m-%d %H:%M:%S') if record.create_date else None
                }
            }
            
        except Exception as e:
            _logger.error('Error in create_test_post API: %s', str(e))
            return {
                "success": False,
                "error": str(e),
                "error_code": "INTERNAL_ERROR"
            }

    @http.route('/api/test_post/get/<int:record_id>', type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_test_post(self, record_id, **kwargs):
        """
        GET API to retrieve a specific record
        
        Endpoint: http://your-domain:port/api/test_post/get/{id}
        Method: GET
        """
        try:
            record = request.env['test.post.api'].sudo().browse(record_id)
            
            if not record.exists():
                return {
                    "success": False,
                    "error": "Record not found",
                    "error_code": "NOT_FOUND"
                }
            
            return {
                "success": True,
                "data": record._get_record_info()
            }
            
        except Exception as e:
            _logger.error('Error in get_test_post API: %s', str(e))
            return {
                "success": False,
                "error": str(e),
                "error_code": "INTERNAL_ERROR"
            }

    @http.route('/api/test_post/list', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def list_test_posts(self, **kwargs):
        """
        GET API to retrieve all records with pagination
        
        Endpoint: http://your-domain:port/api/test_post/list
        Method: POST
        
        Request (optional):
        {
            "jsonrpc": "2.0",
            "params": {
                "limit": 10,
                "offset": 0
            }
        }
        """
        try:
            limit = kwargs.get('limit', 100)
            offset = kwargs.get('offset', 0)
            
            records = request.env['test.post.api'].sudo().search([], limit=limit, offset=offset)
            total_count = request.env['test.post.api'].sudo().search_count([])
            
            data = [record._get_record_info() for record in records]
            
            return {
                "success": True,
                "data": data,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            _logger.error('Error in list_test_posts API: %s', str(e))
            return {
                "success": False,
                "error": str(e),
                "error_code": "INTERNAL_ERROR"
            }