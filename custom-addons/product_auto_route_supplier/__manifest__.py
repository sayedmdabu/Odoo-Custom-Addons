# -*- coding: utf-8 -*-
{
    'name': 'Product Auto Route & Supplier Management',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Automatic routing, vendor mapping, purchase price rules, and sales discount automation',
    'description': """
Product Auto Route & Supplier Management
=========================================
Features:
• Price Group Rate management  
• Manufacturer Rate management  
• Auto sales discount based on rate masters  
""",
    'author': 'SAGBRAIN CORPORATION / Md Abu Sayed',
    'website': 'https://sagbrain.com',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'product',
        'purchase',
        'sale',
        'stock',
        'purchase_stock',
        'stock_route_mto',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',

        # Views
        'views/supplier_external_mapping_views.xml',
        'views/price_group_rate_views.xml',
        'views/maker_rate_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',

        'views/menu_views.xml',
    ],

    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
