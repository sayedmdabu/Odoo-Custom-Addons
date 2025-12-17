# Installation Guide - DOG API Integration

This guide provides step-by-step instructions for installing and configuring the DOG API Integration module for Odoo 18.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Initial Configuration](#initial-configuration)
4. [Partner Setup](#partner-setup)
5. [Product Setup](#product-setup)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- Odoo 18.0 (Community or Enterprise)
- Python 3.10 or higher
- Internet connectivity for API calls
- Access to DOG API staging/production endpoint

### Required Odoo Modules
The following modules must be installed before installing DOG API Integration:
- `purchase` - Purchase Management
- `stock` - Inventory Management

### Python Dependencies
The module uses these Python libraries (usually pre-installed with Odoo):
- `requests` - For HTTP API calls
- `json` - For JSON processing

If not installed:
```bash
pip install requests
```

---

## Installation Steps

### Step 1: Download the Module

Copy the `dog_api_integration` folder to your Odoo addons directory.

**For development/testing:**
```bash
cp -r dog_api_integration /path/to/odoo/custom-addons/
```

**For production:**
```bash
sudo cp -r dog_api_integration /opt/odoo/custom-addons/
sudo chown -R odoo:odoo /opt/odoo/custom-addons/dog_api_integration
```

### Step 2: Update Addons Path

Ensure your addons path includes the directory containing the module.

Edit `odoo.conf`:
```ini
[options]
addons_path = /opt/odoo/addons,/opt/odoo/custom-addons
```

### Step 3: Restart Odoo Server

Restart the Odoo server to recognize the new module:

```bash
# For systemd
sudo systemctl restart odoo

# Or manually
sudo service odoo-server restart

# For development
./odoo-bin -c /path/to/odoo.conf
```

### Step 4: Update Apps List

1. Log in to Odoo as Administrator
2. Go to **Apps** menu
3. Click **Update Apps List**
4. In the dialog, click **Update**

### Step 5: Install the Module

1. In the Apps menu, remove the "Apps" filter
2. Search for "DOG API Integration"
3. Click **Install** button

The module will install along with its dependencies.

---

## Initial Configuration

### Verify Installation

After installation, verify the module is working:

1. Go to **Purchase > Orders > Purchase Orders**
2. Open any purchase order
3. You should see:
   - "Send to DOG API" button in the header
   - "Delivery Mode" field after supplier
   - "DOG Integration" tab in the notebook

### API Configuration

The module comes pre-configured with DOG staging API:

**Current Settings:**
- URL: `https://stage.scm-bio.net/api/odoo/create/index.php`
- Username: `odoo`
- Password: `oaJE2@5V`

**To Change API Settings:**

Edit `/models/purchase_order.py`:

```python
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    # DOG API Configuration
    DOG_API_URL = "https://your-api-url.com/endpoint"
    DOG_API_USERNAME = "your_username"
    DOG_API_PASSWORD = "your_password"
```

After changing, update the module:
```bash
# CLI method
odoo-bin -u dog_api_integration -d your_database

# Or from UI: Apps > DOG API Integration > Upgrade
```

---

## Partner Setup

For the integration to work properly, partners must have specific fields configured.

### Company Partner Setup

1. Go to **Settings > Companies > [Your Company]**
2. Click **Update Info**
3. In the **Related Partner** form, fill:
   - **Reference** (ref): Your company code (e.g., "COMP001")
   - **Name**: Your company name
   - Complete address fields

### Supplier Setup

For each supplier:

1. Go to **Purchase > Configuration > Suppliers**
2. Open the supplier
3. Fill required fields:
   - **Reference** (ref): Supplier code (e.g., "SUP001") - **REQUIRED**
   - **Name**: Supplier name - **REQUIRED**
   - Address fields (recommended)
   - Phone/Email (recommended)

**Quick Setup Script (optional):**
```python
# Run from Odoo shell or scheduled action
suppliers = self.env['res.partner'].search([('supplier_rank', '>', 0)])
for idx, supplier in enumerate(suppliers, 1):
    if not supplier.ref:
        supplier.ref = f'SUP{str(idx).zfill(4)}'
```

### Customer/Ship-to Partner Setup

For direct shipment scenarios:

1. Go to **Contacts**
2. Open the customer/delivery address
3. Fill required fields:
   - **Reference** (ref): Customer code - **REQUIRED for direct ship**
   - **Name**: Customer name - **REQUIRED**
   - **Address Type**: Set to "Delivery Address" or "Other"
   - **ZIP/Postal Code** - **REQUIRED for direct ship**
   - **State** - Recommended
   - **City** - **REQUIRED for direct ship**
   - **Street** - **REQUIRED for direct ship**
   - **Street2** - Optional
   - **Phone** - Recommended

---

## Product Setup

### Configure Products

For each product:

1. Go to **Purchase > Products > Products**
2. Open the product
3. Fill:
   - **Internal Reference** (default_code): Product code (e.g., "PROD-001") - **REQUIRED**
   - **Name**: Product name - **REQUIRED**

### Japanese Product Names (Optional)

To add Japanese translations:

1. Open the product
2. Click **Edit**
3. Click **⚙ > Translations** next to the "Name" field
4. Add translation for **Japanese (ja_JP)**
5. Save

**Bulk Translation Script (optional):**
```python
# Run from Odoo shell
products = self.env['product.product'].search([])
for product in products:
    # Your translation logic here
    product.with_context(lang='ja_JP').write({
        'name': 'Japanese name here'
    })
```

---

## Testing

### Test Purchase Order

Create a test purchase order to verify the integration:

#### Step 1: Create Purchase Order

1. Go to **Purchase > Orders > Purchase Orders**
2. Click **Create**
3. Fill required fields:
   - **Supplier**: Select a supplier with proper ref
   - **Delivery Mode**: Choose "Company Delivery" or "Direct Shipment"
   - If "Direct Shipment": Select **Ship to Partner**
   - **Order Date**: Today's date

#### Step 2: Add Order Lines

1. Click **Add a line**
2. Select product (must have default_code)
3. Fill:
   - **Quantity**: e.g., 10
   - **Unit Price**: e.g., 1500
4. Add more lines as needed

#### Step 3: Confirm Order

1. Click **Confirm Order**
2. The order will automatically be sent to DOG API
3. Check the **DOG Integration** tab:
   - **Exported to DOG**: Should be checked
   - **DOG Export Status**: Should be "Success"
   - **DOG Export Date**: Should show current timestamp
   - **DOG Export Message**: Should show API response

#### Step 4: Manual Resend (Optional)

1. Click **Send to DOG API** button
2. Confirm the action
3. Check the DOG Integration tab for updated status

### Test API Independently

Use the provided test script:

```bash
cd dog_api_integration
python test_dog_api.py
```

This will:
1. Create sample test data
2. Validate all required fields
3. Ask for confirmation
4. Send to DOG API
5. Display results

---

## Troubleshooting

### Common Issues

#### Issue 1: Module Not Appearing in Apps List

**Solution:**
1. Check addons path in odoo.conf
2. Restart Odoo server
3. Update apps list
4. Remove "Apps" filter in search

#### Issue 2: "Send to DOG API" Button Not Visible

**Solution:**
1. Confirm order first (button only appears in purchase/done state)
2. Check user has "Purchase User" access rights
3. Upgrade the module

#### Issue 3: Export Status = Failed

**Possible Causes:**
- Missing required fields
- API connection issue
- Invalid credentials

**Solution:**
1. Check DOG Export Message for error details
2. Verify all required fields:
   ```sql
   -- Check supplier ref
   SELECT id, name, ref FROM res_partner WHERE id = [supplier_id];
   
   -- Check company partner ref
   SELECT id, name, ref FROM res_partner WHERE id IN 
       (SELECT partner_id FROM res_company WHERE id = [company_id]);
   
   -- Check product default_code
   SELECT id, name, default_code FROM product_product WHERE id = [product_id];
   ```
3. Check server logs:
   ```bash
   tail -f /var/log/odoo/odoo-server.log | grep "DOG API"
   ```

#### Issue 4: API Connection Timeout

**Solution:**
1. Check internet connectivity
2. Verify API URL is accessible:
   ```bash
   curl -i https://stage.scm-bio.net/api/odoo/create/index.php
   ```
3. Check firewall settings
4. Increase timeout in code if needed (default: 30 seconds)

#### Issue 5: Authentication Failed

**Solution:**
1. Verify credentials are correct
2. Test with curl:
   ```bash
   curl -X POST https://stage.scm-bio.net/api/odoo/create/index.php \
     -H "Content-Type: application/json" \
     -H "Authorization: Basic b2RvbzpvYUpFMkA1Vg==" \
     -d '{"data":[{"po_number":"TEST"}]}'
   ```
3. Check if password needs updating

#### Issue 6: Missing Fields in Export

**Solution:**
1. Check field mapping in `_prepare_dog_api_data` method
2. Verify custom fields exist:
   ```sql
   SELECT name FROM ir_model_fields 
   WHERE model = 'purchase.order' 
   AND name LIKE 'x_%';
   ```
3. Upgrade module to ensure custom fields are created

### Debug Mode

Enable detailed logging:

1. Edit `models/purchase_order.py`
2. Ensure logging is set to DEBUG:
   ```python
   _logger = logging.getLogger(__name__)
   _logger.setLevel(logging.DEBUG)
   ```
3. Restart Odoo
4. Check logs for detailed API requests/responses

### Check Logs

View detailed logs:

```bash
# Real-time log viewing
tail -f /var/log/odoo/odoo-server.log

# Filter DOG-related logs
grep "DOG API" /var/log/odoo/odoo-server.log

# Last 100 DOG-related logs
grep "DOG API" /var/log/odoo/odoo-server.log | tail -100
```

---

## Verification Checklist

Before going live, verify:

- [ ] Module installed successfully
- [ ] All suppliers have `ref` filled
- [ ] Company partner has `ref` filled
- [ ] All products have `default_code` filled
- [ ] Test purchase order created and confirmed
- [ ] Export status shows "Success"
- [ ] DOG Integration tab shows export date and message
- [ ] API logs show successful requests
- [ ] DOG system received the data correctly
- [ ] Manual resend button works
- [ ] Failed orders can be retried
- [ ] Direct shipment scenario tested (if applicable)

---

## Production Deployment

Before deploying to production:

1. **Backup Database**
   ```bash
   pg_dump odoo_production > backup_before_dog_integration.sql
   ```

2. **Update API Credentials** (if different from staging)
   - Edit API URL, username, password in code
   - Test with production credentials

3. **Update Module**
   ```bash
   odoo-bin -u dog_api_integration -d production_db
   ```

4. **Verify Configuration**
   - Run through verification checklist
   - Test with 1-2 real orders

5. **Monitor Logs**
   ```bash
   tail -f /var/log/odoo/odoo-server.log | grep "DOG API"
   ```

6. **User Training**
   - Train purchase team on new fields
   - Explain delivery mode options
   - Show how to check export status
   - Demonstrate manual resend

---

## Support

For additional help:

- **Email**: support@sagbrain.com
- **Developer**: Md Abu Sayed
- **Company**: SAGBRAIN CORPORATION
- **Documentation**: See README.md in module directory

---

## Appendix

### Required Field Summary

**Purchase Order:**
- Supplier (with ref)
- Order Date
- At least one order line

**Purchase Order Line:**
- Product (with default_code)
- Quantity
- Unit Price

**For Direct Shipment:**
- Ship to Partner (with ref, zip, city, street)

**Company Configuration:**
- Company Partner Reference (ref)

---

**Last Updated**: December 16, 2024
**Version**: 18.0.1.0.0
