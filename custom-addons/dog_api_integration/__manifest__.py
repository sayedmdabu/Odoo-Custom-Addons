# -*- coding: utf-8 -*-
{
    'name': 'DOG API Integration for Purchase Orders',
    'version': '18.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Integrate Purchase Orders with DOG System via API',
    'description': """
        This module automatically sends purchase order data to DOG system when orders are confirmed.
        
        Features:
        - Automatic API call on purchase order confirmation
        - Manual resend button for failed/existing orders
        - Complete field mapping as per specification
        - Error handling and logging
        - Support for direct shipment and company delivery
    """,
    'author': 'SAGBRAIN CORPORATION',
    'website': 'https://www.sagbrain.com',
    'depends': ['purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
