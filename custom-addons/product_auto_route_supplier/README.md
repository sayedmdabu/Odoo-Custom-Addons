# Product Auto Route & Supplier Management

## Overview

This Odoo 18 Community Edition module provides comprehensive automation for product management, supplier relationships, and pricing:

- **Automatic Route Assignment**: Assigns Buy and Make To Order (MTO) routes to products
- **Vendor Mapping**: Maps external supplier codes to Odoo vendors
- **Intelligent Pricing**: Calculates purchase prices using configurable rate masters
- **Automatic Supplier Info**: Creates and updates product.supplierinfo records
- **Sales Discount Application**: Automatically applies discounts when selling products based on rate masters

## Requirements

### Odoo Modules
- `base`
- `product`
- `purchase`
- `sale`
- `stock`
- `purchase_stock`
- `stock_route_mto` (OCA module - **REQUIRED** for MTO functionality)
- `mail`

### OCA Module Installation

This module requires the OCA `stock_route_mto` module to provide Make To Order functionality in Odoo Community Edition:

```bash
# Clone OCA stock-logistics-workflow repository
cd /path/to/odoo/addons
git clone https://github.com/OCA/stock-logistics-workflow.git -b 18.0

# Or install specific module
# Install stock_route_mto from OCA
```

## Installation

1. Copy this module to your Odoo addons directory
2. Install OCA `stock_route_mto` module first
3. Update apps list: `Settings > Apps > Update Apps List`
4. Search for "Product Auto Route & Supplier Management"
5. Click "Install"

## Configuration

### 1. External Supplier Mapping

Navigate to: **Configuration > External Mappings > External Code → Vendor Conversion**

This table maps external supplier codes to Odoo vendors.

**Fields:**
- **External Company Code** (required): Supplier code from external system
- **External Company Name**: Supplier name for reference
- **Vendor (Odoo)** (required): res.partner with supplier rank > 0
- **Priority**: Lower number = higher priority (default: 10)
- **Active**: Only active records are used
- **Notes**: Operational notes

**Example:**
```
External Code: COSMO001
External Name: CosmoB io Japan
Vendor: CosmoB io K.K.
Priority: 10
Active: ✓
```

### 2. Price Group Rate Master

Navigate to: **Configuration > Rate Master > Price Group Rate**

Configure discount rates by price group and supplier.

**Fields:**
- **Supplier Code** (required): External supplier code
- **Price Group Name** (required): Price group identifier
- **Multiplier Rate** (required): Rate (e.g., 0.75 = 25% discount)
- **Discount %**: Auto-calculated from rate
- **Valid From/To**: Optional validity period
- **Active**: Only active records are used
- **Notes**: Remarks

**Example:**
```
Supplier Code: COSMO001
Group Name: PREMIUM
Rate: 0.75 (= 25% discount)
Valid From: 2025-01-01
Valid To: 2025-12-31
Active: ✓
```

### 3. Manufacturer Rate Master

Navigate to: **Configuration > Rate Master > Manufacturer Rate**

Configure discount rates by manufacturer and supplier.

**Fields:**
- **Supplier Code** (required): External supplier code
- **Manufacturer Name** (required): Maker name
- **Discount Rate** (required): Rate (e.g., 0.80 = 20% discount)
- **Discount %**: Auto-calculated from rate
- **Valid From/To**: Optional validity period
- **Active**: Only active records are used
- **Notes**: Remarks

**Example:**
```
Supplier Code: COSMO001
Manufacturer: Thermo Fisher
Rate: 0.80 (= 20% discount)
Valid From: 2025-01-01
Active: ✓
```

## Product Fields

### External API Fields

Add these fields to `product.template` when syncing from external systems:

| Field | Type | Description |
|-------|------|-------------|
| `api_sku` | Char | Product SKU from external system |
| `api_supplier_sku` | Char | Supplier-specific SKU |
| `api_price_group` | Char | Price group for rate determination |
| `api_maker` | Char | Manufacturer name |
| `api_supplier_comp_code` | Char | External supplier code (maps to vendor) |
| `api_supplier_comp_name` | Char | Supplier name |
| `api_sales_origin_maker_name` | Char | Original maker name |
| `api_volume` | Char | Volume specification |
| `api_list_price` | Float | List price from external system |
| `purchase_price_fixed` | Float | Fixed purchase price (highest priority) |

### Auto-Processing Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `auto_process_status` | Selection | pending / processing / success / error |
| `auto_process_message` | Text | Processing log messages |

## Automatic Processing

### When Products Are Created/Updated

When a product with external API fields is created or updated, the system automatically:

1. **Assigns Routes**
   - Buy route (standard)
   - Make To Order route (OCA module)

2. **Identifies Vendor**
   - Uses `api_supplier_comp_code` to lookup vendor
   - Searches `supplier.external.mapping` table

3. **Calculates Purchase Price** (Priority order)
   - ① Fixed Purchase Price (`purchase_price_fixed`)
   - ② Price Group Rate: `list_price × group_rate`
   - ③ Manufacturer Rate: `list_price × maker_rate`
   - ④ Fallback: `list_price × 1.0`

4. **Creates/Updates Supplier Info**
   - Upserts `product.supplierinfo` record
   - Links vendor and calculated price

### Manual Reprocessing

Click the **Reprocess** button on product form to manually trigger auto-processing.

## Sales Discount Application

### Automatic Discount on Sales Orders

When adding a product to a sale order line, the system automatically applies discounts based on:

**Priority:**
1. **Price Group Rate**: If product has `api_supplier_comp_code` and `api_price_group`
2. **Manufacturer Rate**: If product has `api_supplier_comp_code` and `api_maker`
3. **No Discount**: If no matching rate found

The discount percentage is automatically populated in the sale order line's `discount` field.

### Discount Tracking

Sale order lines track the applied discount:

| Field | Description |
|-------|-------------|
| `applied_rate_source` | Source: fixed / price_group / maker / manual |
| `applied_rate_value` | The rate value that was applied |

### Reapplying Discounts

**On Sale Order:**
- Click **Reapply Auto Discounts** button to update all lines

**On Sale Order Lines:**
- Select lines in list view
- Action menu: **Reapply Automatic Discount**

## Usage Examples

### Example 1: External Product Sync

```python
# External API sync creates product
product = env['product.template'].create({
    'name': 'Anti-CD3 Antibody',
    'api_sku': 'CD3-001',
    'api_supplier_comp_code': 'COSMO001',
    'api_price_group': 'PREMIUM',
    'api_maker': 'Thermo Fisher',
    'api_list_price': 50000.00,
    'list_price': 50000.00,
})

# System automatically:
# 1. Assigns Buy + MTO routes
# 2. Maps COSMO001 → CosmoB io K.K. vendor
# 3. Finds PREMIUM rate = 0.75
# 4. Calculates purchase price = 50000 × 0.75 = 37500
# 5. Creates supplierinfo with price 37500
```

### Example 2: Sales Order with Auto Discount

```python
# Create sale order
sale_order = env['sale.order'].create({
    'partner_id': customer_id,
})

# Add product to order line
line = env['sale.order.line'].create({
    'order_id': sale_order.id,
    'product_id': product.product_variant_id.id,
    'product_uom_qty': 10,
})

# System automatically:
# 1. Checks api_supplier_comp_code = COSMO001
# 2. Checks api_price_group = PREMIUM
# 3. Finds rate = 0.75 (25% discount)
# 4. Sets line.discount = 25.0
# 5. Sets line.applied_rate_source = 'price_group'
```

### Example 3: Manual Price Override

```python
# Product with fixed purchase price
product.write({
    'purchase_price_fixed': 35000.00,
})

# Click Reprocess button
product.action_reprocess_product()

# System updates:
# - supplierinfo.price = 35000 (ignores rate masters)
# - auto_process_status = 'success'
# - auto_process_message = "Using fixed purchase price: 35000"
```

## Rate Calculation Logic

### Purchase Price Priority

```
1. IF purchase_price_fixed > 0:
      RETURN purchase_price_fixed
      
2. IF api_supplier_comp_code AND api_price_group:
      rate = price.group.rate.get_rate(supplier_code, price_group)
      IF rate:
          RETURN list_price × rate
          
3. IF api_supplier_comp_code AND api_maker:
      rate = maker.rate.get_rate(supplier_code, maker)
      IF rate:
          RETURN list_price × rate
          
4. RETURN list_price × 1.0  # Fallback
```

### Sales Discount Priority

```
1. IF api_supplier_comp_code AND api_price_group:
      rate = price.group.rate.get_rate(supplier_code, price_group)
      IF rate:
          discount_percent = (1.0 - rate) × 100
          RETURN discount_percent
          
2. IF api_supplier_comp_code AND api_maker:
      rate = maker.rate.get_rate(supplier_code, maker)
      IF rate:
          discount_percent = (1.0 - rate) × 100
          RETURN discount_percent
          
3. RETURN 0.0  # No discount
```

## Error Handling

### Common Issues

**Issue**: Vendor not found
- **Solution**: Add mapping in External Code → Vendor Conversion
- **Log**: "Supplier mapping not found for code: XXX"

**Issue**: MTO route not assigned
- **Solution**: Install OCA `stock_route_mto` module
- **Message**: "Warning: MTO route not found. Install OCA stock_route_mto module."

**Issue**: Price not calculated
- **Solution**: Add rate master or set `purchase_price_fixed`
- **Fallback**: Uses `list_price × 1.0`

**Issue**: Discount not applied on sales
- **Reason**: Manual discount already set, or no rate master found
- **Solution**: Click "Reapply Auto Discounts" or configure rate master

## Logging

The module logs extensively for troubleshooting:

```python
import logging
_logger = logging.getLogger(__name__)

# View logs in Odoo:
# Settings > Technical > Database Structure > Logs
```

**Log Levels:**
- `INFO`: Successful operations, vendor mappings, price calculations
- `WARNING`: Missing mappings, expired rates, fallback usage
- `ERROR`: Processing failures, exceptions
- `DEBUG`: Detailed processing steps

## API Integration

### External System Sync

When syncing products from external systems, populate these fields:

```python
{
    'api_sku': external_data['sku'],
    'api_supplier_comp_code': external_data['supplier_comp_code'],
    'api_supplier_comp_name': external_data['supplier_comp_name'],
    'api_price_group': external_data['price_group'],
    'api_maker': external_data['maker_name'],
    'api_supplier_sku': external_data['supplier_sku'],
    'api_sales_origin_maker_name': external_data['sales_origin_maker_name'],
    'api_volume': external_data['volume'],
    'api_list_price': external_data['list_price'],
    'purchase_price_fixed': external_data.get('purchase_price_fixed', False),
    'name': external_data['product_name'],
    'list_price': external_data['list_price'],
    'sale_ok': True,
    'purchase_ok': True,
}
```

Auto-processing triggers automatically on create/write.

## Support

For issues, questions, or feature requests:
- **Developer**: SAGBRAIN CORPORATION
- **Website**: https://sagbrain.com
- **Email**: support@sagbrain.com

## License

LGPL-3

## Changelog

### Version 18.0.1.0.0
- Initial release
- Automatic route assignment (Buy + MTO)
- External supplier code mapping
- Price group rate master
- Manufacturer rate master
- Automatic purchase price calculation
- Automatic supplier info creation
- **NEW**: Automatic sales discount application
- **NEW**: Discount tracking on sale order lines
- **NEW**: Manual discount reapplication
- Processing status tracking
- Comprehensive logging
