# ========================================
# FILE: ordia/__manifest__.py
# ========================================
{
    'name': 'ORDIA Integration',
    'version': '18.0.1.0.0',
    'category': 'Integration',
    'summary': 'ORDIA API Integration for Cart Management',
    'description': """
        ORDIA Integration Module
        ========================
        * Login with ORDIA API credentials
        * View and search cart data
        * Real-time API integration
    """,
    'author': 'Md Abu Sayed',
    'website': 'https://www.sagbrain.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/ordia_login_views.xml',
        'views/ordia_cart_views.xml',
        'views/ordia_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}