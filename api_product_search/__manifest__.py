# -*- coding: utf-8 -*-
{
    'name': 'API Product Search',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Search products from external API in sales orders',
    'description': 'Integrates with external API to search products in sales order lines',
    'author': 'Md Abu Sayed Sagbrain',
    'website': 'https://sagbrain.com',
    'sequence': 3,
    'depends': ['sale', 'product'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
