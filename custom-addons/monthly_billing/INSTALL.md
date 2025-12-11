# Monthly Billing Module - Installation & Verification Guide

## Module Structure Verification

The module contains the following files:

### Python Files
- `__init__.py` - Main module initialization
- `__manifest__.py` - Module manifest
- `models/__init__.py` - Models initialization
- `models/res_partner.py` - Partner extension
- `models/monthly_billing_header.py` - Main billing header model
- `models/monthly_billing_line.py` - Billing line model
- `wizards/__init__.py` - Wizards initialization
- `wizards/monthly_billing_generate_wizard.py` - Generation wizard

### XML Files
- `data/sequence.xml` - Sequence configuration
- `security/monthly_billing_security.xml` - Security groups and rules
- `security/ir.model.access.csv` - Access control list
- `views/monthly_billing_header_views.xml` - Header views (tree, form, search)
- `views/monthly_billing_wizard_views.xml` - Wizard views
- `views/monthly_billing_menu.xml` - Menu structure
- `report/monthly_billing_report.xml` - Report definition
- `report/monthly_billing_report_template.xml` - QWeb report template

### Translation Files
- `i18n/ja.po` - Japanese translation

### Documentation
- `README.md` - Module documentation
- `static/description/index.html` - Module description for apps page

## Installation Steps

### 1. Copy Module to Addons Directory

```bash
# Copy the entire monthly_billing folder to your Odoo addons directory
cp -r monthly_billing /path/to/odoo/addons/
```

### 2. Update Odoo Configuration (Optional)

Add the addons path to your Odoo configuration file if not already present:

```ini
[options]
addons_path = /path/to/odoo/addons,/path/to/custom/addons
```

### 3. Restart Odoo Server

```bash
# Stop Odoo
sudo systemctl stop odoo

# Start Odoo with update flag
sudo systemctl start odoo
# OR run manually with update
/path/to/odoo-bin -c /path/to/odoo.conf -u all -d your_database
```

### 4. Activate Developer Mode

In Odoo:
1. Go to Settings
2. Activate Developer Mode (at the bottom of the page)

### 5. Update Apps List

1. Navigate to Apps menu
2. Click "Update Apps List" button
3. Confirm the update

### 6. Install the Module

1. Search for "Monthly Billing" in the Apps menu
2. Click Install

## Verification Steps

### 1. Check Menu Access

After installation, verify the following menu items appear:

- **Invoicing** (or Accounting)
  - **Monthly Billing**
    - Monthly Billings
    - Generate Monthly Billing

### 2. Verify User Groups

Go to Settings → Users & Companies → Groups:
- Monthly Billing / User
- Monthly Billing / Manager

### 3. Test Customer Configuration

1. Go to Contacts
2. Open any customer
3. Verify new fields appear:
   - Closing Day
   - Closing Type
   - Billing Group Code

### 4. Test Wizard

1. Go to Invoicing → Monthly Billing → Generate Monthly Billing
2. Verify the wizard form opens with:
   - Closing Year/Month field
   - Closing Day field
   - Period date calculation
   - Customer selection
   - Preview button

### 5. Test Report

1. Create a test monthly billing (or use the wizard)
2. Click "Print PDF" button
3. Verify PDF generates with proper formatting

## Quick Test Scenario

### Prerequisites
- At least one customer configured
- At least one posted invoice (out_invoice)

### Test Steps

1. **Configure Customer**
   - Go to Contacts → Select a customer
   - Set "Closing Day" = 31 (End of Month)
   - Save

2. **Create Test Invoice**
   - Go to Invoicing → Customers → Invoices
   - Create a new invoice for the customer
   - Add invoice lines
   - Post the invoice

3. **Generate Monthly Billing**
   - Go to Invoicing → Monthly Billing → Generate Monthly Billing
   - Set Closing Year/Month to current month (e.g., 2025-01)
   - Set Closing Day to 31
   - Leave customer selection empty (or select your test customer)
   - Select "Posted Only"
   - Click "Preview" to see estimated results
   - Click "Generate Monthly Billing"

4. **Review Generated Billing**
   - You should be redirected to the generated monthly billing(s)
   - Verify the header shows correct amounts
   - Verify invoice lines are populated correctly
   - Click "Confirm" to change state to Confirmed
   - Click "Print PDF" to generate the statement

5. **Verify PDF Report**
   - Open the downloaded PDF
   - Verify it contains:
     - Company information
     - Customer information
     - Period dates
     - Amount summary
     - Invoice line details
     - Bilingual headers (English/Japanese)

## Troubleshooting

### Module Not Appearing in Apps List

1. Verify the module is in the correct addons path
2. Check Odoo logs for errors
3. Ensure __manifest__.py is valid Python
4. Run with `-u monthly_billing` flag:
   ```bash
   /path/to/odoo-bin -c config.conf -u monthly_billing -d database_name
   ```

### Import Errors

1. Check Python version (requires 3.10+)
2. Verify all dependencies are installed:
   - base
   - account
   - contacts

### Permission Issues

1. Verify user is in the correct security group
2. Check ir.model.access.csv is loaded correctly
3. Review security rules in monthly_billing_security.xml

### No Invoices Found in Wizard

1. Verify invoices exist in the specified period
2. Check invoice dates fall within calculated period
3. Verify invoice state matches filter (posted/draft)
4. Check company_id matches

## Database Migration Notes

If upgrading from a previous version or moving between environments:

1. Always backup your database first
2. Use Odoo's update mechanism: `-u monthly_billing`
3. Check for data model changes
4. Verify sequence continues from correct number

## Support

For issues or questions:
1. Check Odoo logs: `/var/log/odoo/odoo-server.log`
2. Enable debug mode for detailed error messages
3. Review README.md for detailed documentation
4. Contact your system administrator

## Module Information

- **Name**: Monthly Billing
- **Version**: 18.0.1.0.0
- **License**: LGPL-3
- **Odoo Version**: 18.0
- **Depends**: base, account, contacts

---

Last Updated: 2025-01-01
