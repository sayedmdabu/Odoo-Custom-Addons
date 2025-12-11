# -*- coding: utf-8 -*-
{
    'name': 'Monthly Billing',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Japanese-style closing date-based monthly billing',
    'description': """
Monthly Billing Module for Odoo 18
===================================
This module implements Japanese-style closing date-based monthly billing (まとめ請求).

Features:
---------
* Aggregate invoices by closing period and customer
* Generate monthly billing statements
* Support for different closing dates (end-of-month, 20th, etc.)
* PDF report generation
* Multi-company support
* Full i18n support (Japanese/English)

Compatible with Odoo 18 Community Edition and Enterprise Edition.
    """,
    'author': 'SAGBRAIN CORPORATION / Md Abu Sayed',
    'website': 'https://sagbrain.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'account',
        'contacts',
    ],
    'data': [
        # Security
        'security/monthly_billing_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence.xml',
        'data/pdf_config_data.xml',
        
        # Views
        'views/monthly_billing_header_views.xml',
        'views/monthly_billing_wizard_views.xml',
        'views/monthly_billing_pdf_config_views.xml',
        'views/monthly_billing_menu.xml',
        
        # Reports
        'report/monthly_billing_report.xml',
        'report/monthly_billing_report_template.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
