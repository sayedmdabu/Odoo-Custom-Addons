
# Odoo 18 API Development Guide

## 1. Overview
This guide explains how to create custom REST APIs (both **POST** and **GET**) in Odoo 18. It includes examples for model creation, access control, controller setup, and testing.

---

## 2. Module Structure
```
test_post_api/
│
├── __manifest__.py
├── __init__.py
├── models/
│   └── test_post_api.py
├── controllers/
│   └── api_controller.py
└── security/
    └── ir.model.access.csv
```

---

## 3. Module Manifest
Defines metadata and dependencies for the module.

```python
{
    'name': 'Test Post API',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Store data via custom POST API in Odoo 18',
    'author': 'Md Abu Sayed - Sagbrain',
    'website': 'https://www.sagbrain.com',
    'depends': ['base'],
    'data': ['security/ir.model.access.csv'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

---

## 4. Model Definition
Defines fields, validations, and helper methods for record serialization.

```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class TestPostApi(models.Model):
    _name = 'test.post.api'
    _description = 'Test Post API'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    note = fields.Text(string='Note')
    active = fields.Boolean(default=True)

    @api.constrains('email')
    def _check_email(self):
        for record in self:
            if record.email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', record.email):
                raise ValidationError('Invalid email format!')

    def _get_record_info(self):
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email or '',
            'phone': self.phone or '',
            'note': self.note or '',
            'active': self.active,
            'created_date': self.create_date.strftime('%Y-%m-%d %H:%M:%S') if self.create_date else '',
        }
```

---

## 5. Access Control
Grants permissions to create, read, and update records.

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_test_post_api_user,test_post_api_user,model_test_post_api,,1,1,1,1
```

---

## 6. Controller (API Routes)
Implements three routes: create, retrieve by ID, and list with pagination.

```python
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class TestApiController(http.Controller):
    @http.route('/api/test_post', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_test_post(self, **post):
        try:
            data = post.get("values", post)
            if not data.get("name"):
                return {"success": False, "error": "Name is required"}
            record = request.env['test.post.api'].sudo().create(data)
            return {"success": True, "data": record._get_record_info()}
        except Exception as e:
            _logger.error('Error: %s', e)
            return {"success": False, "error": str(e)}
```

---

## 7. Testing the API
### POST (Create)
**Endpoint:** `/api/test_post`  
**Method:** `POST`  
**Content-Type:** `application/json`

```json
{
  "jsonrpc": "2.0",
  "params": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "note": "Test note"
  }
}
```

### GET (Retrieve by ID)
**Endpoint:** `/api/test_post/get/1`  
**Method:** `GET`

### POST (List Records)
**Endpoint:** `/api/test_post/list`  
**Method:** `POST`

---

## 8. Example Python Test Script
```python
import requests

url = "http://localhost:8069/api/test_post"
payload = {
    "jsonrpc": "2.0",
    "params": {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "5551234567",
        "note": "Hello from test!"
    }
}
response = requests.post(url, json=payload)
print(response.json())
```

---

## 9. Summary Table

| Feature | Description |
|----------|--------------|
| Model | test.post.api |
| POST Endpoint | /api/test_post |
| GET Endpoint | /api/test_post/get/<id> |
| List Endpoint | /api/test_post/list |
| Auth | public |
| Format | JSON-RPC |
| Tested with | Postman / Python Requests |
