{
    'name': 'Test Post API',
    'version': '1.0.0',
    'category': 'Tools',
    'summary': 'Store data via custom POST API in Odoo 18',
    'description': """
        This module creates a custom POST API endpoint to insert data into Odoo database.
        - Creates test_post_api table
        - Provides /api/test_post endpoint
        - Accepts JSON data via POST requests
    """,
    'author': 'Md Abu Sayed - Sagbrain',
    'website': 'https://www.sagbrain.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
