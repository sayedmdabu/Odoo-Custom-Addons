{
    'name': 'ORDIA Company Extension',
    'version': '18.0.1.0.0',
    'category': 'Settings',
    'summary': 'Add ORDIA Corporate Code field to Companies',
    'description': """
        This module extends the Companies model to add:
        - ORDIA Corporate Code field
    """,
    'author': 'Md Abu Sayed',
    'website': 'https://www.sagbrain.com',
    'depends': ['base'],
    'data': [
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}