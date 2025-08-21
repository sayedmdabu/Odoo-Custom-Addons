{
    "name": "JP Public Holidays",
    "version": "18.0.1.0.1",
    "category": "Localization",
    "summary": "Japan public holidays with CSV import and API fetch",
    "author": "Sagbrain - Md Abu Sayed",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",                 # security first

        "views/jp_holiday_import_wizard_views.xml",     # existing import wizard form
        "views/jp_holiday_filter_wizard_views.xml",     # NEW: filter wizard form (must be before actions)
        "views/jp_actions.xml",                         # actions (import + filter) after their form views

        "views/jp_holiday_views.xml",                   # main list/form views referencing those actions
    ],
    "installable": True,
    "application": True,
}
