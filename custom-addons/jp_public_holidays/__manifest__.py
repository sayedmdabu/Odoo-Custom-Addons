{
    "name": "JP Public Holidays",
    "version": "18.0.1.0.1",
    "summary": "Manage and import Japan public holidays",
    "author": "Sayed Sagbrain",
    "website": "",
    "category": "Human Resources/Localization",
    "license": "LGPL-3",
    "depends": ["base"],
    "external_dependencies": {
        "python": ["requests"]
    },
    "data": [
        "security/ir.model.access.csv",
        "views/jp_holiday_import_wizard_views.xml",
        "views/jp_actions.xml",
        "views/jp_holiday_views.xml",
    ],
    "application": False,
    "installable": True,
}
