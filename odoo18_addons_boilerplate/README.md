# Odoo 18 Addon Boilerplate

A minimal yet complete scaffold you can drop into your `addons` path.

## Install
1. Unzip into your addons directory so the folder is `odoo18_addon_boilerplate/`.
2. Update app list and install **My Custom Module (Boilerplate)**.

## Contents
- `models/` a sample model `my.module`
- `views/` tree+form views, action, and menu
- `wizards/` a modal to quickly create a record
- `controllers/` a demo HTTP route `/my_module/hello`
- `report/` a QWeb PDF report
- `security/` access rights & a basic group
- `data/` a sequence
- `demo/` sample demo records
- `static/src/` example JS/SCSS/QWeb assets
- `tests/` a minimal unit test

## Notes
- Change the module name, namespace, and technical IDs as needed.
- Add dependencies to `__manifest__.py` as required (e.g., `web`, `mail`, etc.).
