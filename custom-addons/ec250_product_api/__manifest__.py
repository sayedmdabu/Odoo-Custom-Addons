# -*- coding: utf-8 -*-
{
    "name": "EC250 Product API Search",
    "summary": "Search & display products from external EC API (token auto-refresh).",
    "version": "18.0.1.0.0",
    "author": "Sagbrain / Md Abu Sayed",
    "website": "https://sagbrain.com",
    "category": "Tools",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/ec250_search_views.xml",
    ],
    "installable": True,
    "application": True,
}
