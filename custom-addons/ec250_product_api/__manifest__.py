# -*- coding: utf-8 -*-
{
    "name": "EC250 Product API Search",
    "summary": "Search & display products from external EC API (token auto-refresh).",
    "version": "18.0.1.0.1",
    "author": "Md Abu Sayed",
    "website": "https://sagbrain.com",
    "category": "Tools",
    "license": "LGPL-3",
    "sequence": 1,
    "depends": ["base", "sale_management", "product", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/ec250_search_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": True,
}
