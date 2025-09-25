{
    'name': 'My Custom Module (Boilerplate)',
    'version': '18.0.1.0.0',
    'summary': 'Starter boilerplate for Odoo 18 addons',
    'description': 'A minimal yet complete Odoo 18 addon scaffold with models, views, security, data, wizards, controllers, and static assets.',
    'author': 'You',
    'website': 'https://example.com',
    'category': 'Tools',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/my_model_views.xml',
        'views/menu.xml',
        'wizards/wizard_views.xml',
        'report/report.xml',
        'report/report_templates.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo18_addon_boilerplate/static/src/js/my_module.js',
            'odoo18_addon_boilerplate/static/src/scss/my_module.scss',
            'odoo18_addon_boilerplate/static/src/xml/my_module.xml',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
}
