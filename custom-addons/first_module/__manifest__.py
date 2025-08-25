# -*- coding: utf-8 -*-
{
    'name': "First Module",          # The name of your module
    'summary': "Short summary of the module",  
    'description': """
        A detailed description of what your module does.
        You can use multiple lines and even RST/Markdown-style formatting.
    """,
    'author': "Md Abu Sayed / Company",
    'website': "https://sagbrain.com/",

    # Categories help organize modules in Odoo Apps menu
    'category': 'Custom',
    'version': '18.0.1.0.0',   # Odoo Version + Module Version

    # List of dependencies (other Odoo modules your addon needs to work)
    'depends': [
        'base',   # Always include base
        # add others like 'sale', 'account', 'stock'
    ],

    # Data files loaded at installation
    'data': [
        'security/ir.model.access.csv',  # Security access rights
        'views/first_module_views.xml',      # Views
    ],
    # Extra info
    'installable': True,   # Can be installed
    'application': True,   # Shows up as a separate application in Apps menu
    'auto_install': False, # Installed automatically if dependencies are met

    # License
    'license': 'LGPL-3',  # Options: LGPL-3, OPL-1, AGPL-3, etc.
}
