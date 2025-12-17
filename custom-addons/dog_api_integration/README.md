# DOG API Integration for Odoo 18 Purchase Orders

This Odoo 18 addon integrates Purchase Orders with the DOG (Distributor Order Gateway) system via REST API.

## Features

- ✅ **Automatic Export**: Automatically sends purchase order data to DOG API when orders are confirmed
- ✅ **Manual Resend**: Manual button to resend failed or existing orders
- ✅ **Complete Field Mapping**: Maps all 26 fields as per DOG specification
- ✅ **Delivery Mode Support**: Supports both company delivery (自社) and direct shipment (直送)
- ✅ **Error Handling**: Comprehensive error logging and status tracking
- ✅ **Multi-language Support**: Japanese product name support
- ✅ **Status Tracking**: Track export status (Pending/Success/Failed)

## Installation

1. Copy the `dog_api_integration` folder to your Odoo addons directory:
   ```bash
   cp -r dog_api_integration /path/to/odoo/addons/
   ```

2. Update the apps list in Odoo:
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "DOG API Integration"

3. Install the module:
   - Click "Install" button

## Configuration

### API Settings

The module comes pre-configured with DOG API credentials:

- **API URL**: `https://stage.scm-bio.net/api/odoo/create/index.php`
- **Authentication**: Basic Auth
  - Username: `odoo`
  - Password: `oaJE2@5V`

To change these settings, edit the following constants in `models/purchase_order.py`:

```python
DOG_API_URL = "https://stage.scm-bio.net/api/odoo/create/index.php"
DOG_API_USERNAME = "odoo"
DOG_API_PASSWORD = "oaJE2@5V"
```

### Required Custom Fields

The module automatically adds the following custom fields to Purchase Orders:

1. **Delivery Mode** (`x_delivery_mode`):
   - Company Delivery (自社) - Default
   - Direct Shipment to Customer (直送)

2. **Ship to Partner** (`x_ship_to_partner_id`):
   - Required when Delivery Mode = Direct Shipment
   - Select the customer/delivery destination

3. **Export Status Fields**:
   - `export_to_dog`: Boolean flag
   - `dog_export_date`: Export timestamp
   - `dog_export_status`: Success/Failed/Pending
   - `dog_export_message`: API response message

### Partner Configuration

For proper integration, ensure the following fields are filled in partners (res.partner):

**For Supplier (仕入先)**:
- ✅ Reference/Code (`ref`) - Required for `supplier_code`
- ✅ Name - Required for `supplier_name`

**For Company (自社)**:
- ✅ Company Partner Reference (`company_id.partner_id.ref`) - Required for `buyer_code`
- ✅ Company Name - Required for `buyer_name`

**For Ship-to Address (納品先)** (Required for Direct Shipment):
- ✅ Reference/Code (`ref`) - Required for `ship_to_party_code`
- ✅ Name - Required for `ship_to_party_name`
- ✅ Postal Code (`zip`) - Required for `ship_to_zip`
- ✅ State - For `ship_to_state`
- ✅ City - Required for `ship_to_city`
- ✅ Street & Street2 - Required for `ship_to_street`
- ✅ Phone - Optional for `ship_to_phone`

### Product Configuration

For products:
- ✅ Internal Reference (`default_code`) - Required for `item_code`
- ✅ Product Name - Will be used for `item_name`
- ℹ️ Japanese translations can be added via Translations menu

## Usage

### Automatic Export

When you confirm a purchase order:
1. Click "Confirm Order" button
2. The order will be automatically sent to DOG API
3. Check the "DOG Integration" tab for export status

### Manual Export/Resend

For already confirmed orders or to retry failed exports:
1. Open the purchase order
2. Click "Send to DOG API" button in the header
3. Check the "DOG Integration" tab for results

### Monitoring Export Status

**List View**:
- Filter by "Exported to DOG" or "Not Exported to DOG"
- Filter by "Export Failed"
- Group by "DOG Export Status"

**Form View**:
- Check "DOG Integration" tab
- View export date, status, and API response message

## Field Mapping

Complete mapping according to DOG specification:

| No | DOG Field | Odoo Source | Description |
|----|-----------|-------------|-------------|
| 3 | po_number | purchase.order.name | 発注番号 |
| 4 | po_line_number | purchase.order.line.sequence | 発注明細行番号 |
| 5 | order_date | purchase.order.date_order | 発注日 |
| 6 | requested_date | purchase.order.line.date_planned | 納期 |
| 7 | buyer_code | company_id.partner_id.ref | 発注元企業コード |
| 8 | buyer_name | company_id.name | 発注元企業名 |
| 9 | supplier_code | partner_id.ref | 仕入先コード |
| 10 | supplier_name | partner_id.name | 仕入先名 |
| 11 | supplier_quote_number | partner_ref | 見積番号 |
| 12 | delivery_destination_type | x_delivery_mode | 納品区分 (1/2) |
| 13 | ship_to_party_code | ship_to_partner.ref | 納品先コード |
| 14 | ship_to_party_name | ship_to_partner.name | 納品先名 |
| 15 | ship_to_zip | ship_to_partner.zip | 郵便番号 |
| 16 | ship_to_state | ship_to_partner.state_id.name | 都道府県 |
| 17 | ship_to_city | ship_to_partner.city | 市区町村 |
| 18 | ship_to_street | ship_to_partner.street + street2 | 番地・建物 |
| 19 | ship_to_phone | ship_to_partner.phone | 電話番号 |
| 20 | item_code | product_id.default_code | 商品コード |
| 21 | item_name | product_id.name (ja_JP) | 商品名 |
| 22 | ordered_qty | product_qty | 発注数量 |
| 23 | unit_price | price_unit | 単価 |
| 24 | line_amount | price_subtotal | 金額 |
| 25 | po_remark | notes | 備考(ヘッダ) |
| 26 | line_remark | x_line_remark | 備考(明細) |

## API Request Format

```json
{
  "data": [
    {
      "po_number": "PO00045",
      "po_line_number": 10,
      "order_date": "2025-11-18",
      "requested_date": "2025-11-25",
      "buyer_code": "SB01",
      "buyer_name": "SagBrain Corp.",
      "supplier_code": "SUP001",
      "supplier_name": "○○化学株式会社",
      "supplier_quote_number": "QUO-2025-001",
      "delivery_destination_type": "2",
      "ship_to_party_code": "CUST001",
      "ship_to_party_name": "理科研大学",
      "ship_to_zip": "113-0034",
      "ship_to_state": "東京都",
      "ship_to_city": "文京区",
      "ship_to_street": "湯島3-10-8...",
      "ship_to_phone": "03-1234-5678",
      "item_code": "P-00123",
      "item_name": "バッファ溶液A",
      "ordered_qty": 10.0,
      "unit_price": 1500.0,
      "line_amount": 15000.0,
      "po_remark": "先方指定フォーム使用",
      "line_remark": "代替品"
    }
  ]
}
```

## Troubleshooting

### Common Issues

**1. API Connection Failed**
- Check internet connectivity
- Verify API URL is accessible
- Check firewall settings

**2. Authentication Failed**
- Verify username and password
- Check if credentials need updating

**3. Missing Required Fields**
- Ensure supplier has `ref` (code) filled
- Ensure company partner has `ref` filled
- For direct shipment, ensure ship-to partner is selected

**4. Export Status = Failed**
- Check "DOG Integration" tab for error message
- Verify all required fields are filled
- Check server logs for detailed errors

### Logs

Check Odoo logs for detailed error messages:
```bash
tail -f /var/log/odoo/odoo-server.log | grep "DOG API"
```

## Support

For issues or questions:
- **Developer**: Md Abu Sayed
- **Company**: SAGBRAIN CORPORATION
- **Email**: support@sagbrain.com

## Version History

- **v18.0.1.0.0** (2024-12-16)
  - Initial release
  - Complete DOG API integration
  - Support for Odoo 18.0

## License

LGPL-3

---

**Note**: This module requires an active internet connection and valid DOG API credentials to function properly.
