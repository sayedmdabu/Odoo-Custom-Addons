{
    'name': 'Product Customer Reference Search',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Search products by customer reference',
    'description': """
        This module allows users to search for products using a custom field 'Customer Reference'.
    """,
    'author': 'Md Abu Sayed - Sagbrain',
    'website': 'https://sagbrain.com',
    'depends': ['sale', 'product'],
    'data': [
        'views/product_template_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}