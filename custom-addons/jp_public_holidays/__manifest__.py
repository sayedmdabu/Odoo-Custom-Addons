{
    "name": "JP Public Holidays",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "summary": "Japan public holidays with CSV import and API fetch",
    "author": "Sagbrain - Md Abu Sayed",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        # 1) security first
        "security/ir.model.access.csv",

        # 2) wizard VIEW must be loaded before the wizard ACTION that references it
        "views/jp_holiday_import_wizard_views.xml",

        # 3) wizard ACTION (uses the wizard view id)
        "views/jp_actions.xml",

        # 4) main list/form views (these use the wizard ACTION id)
        "views/jp_holiday_views.xml",
    ],
    "installable": True,
    "application": True,
}
