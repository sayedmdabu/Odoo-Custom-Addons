# Testing Guide

## Prerequisites

1. Odoo 18 Community Edition installed
2. OCA `stock_route_mto` module installed
3. This module installed and activated

## Test Scenarios

### Test 1: External Supplier Mapping

**Objective**: Verify external code maps to vendor correctly

**Steps:**
1. Navigate to Configuration > External Mappings > External Code → Vendor Conversion
2. Create new mapping:
   - External Company Code: `TEST001`
   - External Company Name: `Test Supplier Inc.`
   - Vendor: Select/Create a vendor partner
   - Priority: `10`
   - Active: ✓
3. Save

**Expected Result:**
- Record created successfully
- Unique constraint prevents duplicate active codes
- Vendor must have supplier_rank > 0

**Validation:**
```python
# In Odoo shell
mapping = env['supplier.external.mapping'].search([('external_supplier_comp_code', '=', 'TEST001')])
vendor = mapping.get_vendor_from_external_code('TEST001')
print(f"Vendor: {vendor.name}")  # Should print vendor name
```

---

### Test 2: Price Group Rate Master

**Objective**: Configure and retrieve price group rates

**Steps:**
1. Navigate to Configuration > Rate Master > Price Group Rate
2. Create new rate:
   - Supplier Code: `TEST001`
   - Price Group Name: `STANDARD`
   - Multiplier Rate: `0.80` (20% discount)
   - Valid From: Today
   - Valid To: 1 year from today
   - Active: ✓
3. Save

**Expected Result:**
- Discount % shows `20.00%`
- Unique constraint prevents duplicate active supplier+group
- Display name shows: `TEST001 / STANDARD (Rate: 0.8000)`

**Validation:**
```python
# In Odoo shell
rate_model = env['price.group.rate']
rate = rate_model.get_rate('TEST001', 'STANDARD')
print(f"Rate: {rate}")  # Should print 0.8
discount = rate_model.get_discount_percent('TEST001', 'STANDARD')
print(f"Discount: {discount}%")  # Should print 20.0
```

---

### Test 3: Manufacturer Rate Master

**Objective**: Configure and retrieve manufacturer rates

**Steps:**
1. Navigate to Configuration > Rate Master > Manufacturer Rate
2. Create new rate:
   - Supplier Code: `TEST001`
   - Manufacturer Name: `Thermo Fisher`
   - Discount Rate: `0.75` (25% discount)
   - Valid From: Today
   - Active: ✓
3. Save

**Expected Result:**
- Discount % shows `25.00%`
- Unique constraint prevents duplicate active supplier+maker
- Display name shows: `TEST001 / Thermo Fisher (Rate: 0.7500)`

**Validation:**
```python
# In Odoo shell
maker_model = env['maker.rate']
rate = maker_model.get_rate('TEST001', 'Thermo Fisher')
print(f"Rate: {rate}")  # Should print 0.75
discount = maker_model.get_discount_percent('TEST001', 'Thermo Fisher')
print(f"Discount: {discount}%")  # Should print 25.0
```

---

### Test 4: Product Auto-Processing - Fixed Price

**Objective**: Verify fixed purchase price takes priority

**Steps:**
1. Navigate to Inventory > Products > Products
2. Create new product:
   - Name: `Test Product - Fixed Price`
   - API SKU: `TEST-FIX-001`
   - Supplier Company Code: `TEST001`
   - API List Price: `10000`
   - List Price: `10000`
   - **Fixed Purchase Price**: `8000`
   - Can be Sold: ✓
   - Can be Purchased: ✓
3. Save

**Expected Result:**
- Auto Process Status: `Success`
- Routes: Buy and MTO assigned
- Supplier Info created with price = `8000`
- Message shows: "Using fixed purchase price: 8000"

**Validation:**
```python
product = env['product.template'].search([('api_sku', '=', 'TEST-FIX-001')])
print(f"Status: {product.auto_process_status}")
print(f"Message: {product.auto_process_message}")
print(f"Routes: {[r.name for r in product.route_ids]}")
supplierinfo = env['product.supplierinfo'].search([('product_tmpl_id', '=', product.id)])
print(f"Supplier: {supplierinfo.partner_id.name}, Price: {supplierinfo.price}")
```

---

### Test 5: Product Auto-Processing - Price Group Rate

**Objective**: Verify price group rate calculation

**Steps:**
1. Ensure Test 2 (Price Group Rate) is completed
2. Create new product:
   - Name: `Test Product - Price Group`
   - API SKU: `TEST-PG-001`
   - Supplier Company Code: `TEST001`
   - **Price Group**: `STANDARD`
   - API List Price: `10000`
   - List Price: `10000`
   - Can be Sold: ✓
   - Can be Purchased: ✓
3. Save

**Expected Result:**
- Auto Process Status: `Success`
- Supplier Info price = `8000` (10000 × 0.80)
- Message shows: "Using price group rate: 10000 × 0.8000 = 8000"

**Validation:**
```python
product = env['product.template'].search([('api_sku', '=', 'TEST-PG-001')])
supplierinfo = env['product.supplierinfo'].search([('product_tmpl_id', '=', product.id)])
assert supplierinfo.price == 8000, f"Expected 8000, got {supplierinfo.price}"
```

---

### Test 6: Product Auto-Processing - Manufacturer Rate

**Objective**: Verify manufacturer rate calculation

**Steps:**
1. Ensure Test 3 (Manufacturer Rate) is completed
2. Create new product:
   - Name: `Test Product - Manufacturer`
   - API SKU: `TEST-MK-001`
   - Supplier Company Code: `TEST001`
   - **Manufacturer**: `Thermo Fisher`
   - API List Price: `10000`
   - List Price: `10000`
   - Can be Sold: ✓
   - Can be Purchased: ✓
3. Save

**Expected Result:**
- Auto Process Status: `Success`
- Supplier Info price = `7500` (10000 × 0.75)
- Message shows: "Using manufacturer rate: 10000 × 0.7500 = 7500"

**Validation:**
```python
product = env['product.template'].search([('api_sku', '=', 'TEST-MK-001')])
supplierinfo = env['product.supplierinfo'].search([('product_tmpl_id', '=', product.id)])
assert supplierinfo.price == 7500, f"Expected 7500, got {supplierinfo.price}"
```

---

### Test 7: Product Auto-Processing - Priority Order

**Objective**: Verify rate priority: Fixed > Price Group > Manufacturer

**Steps:**
1. Create product with all three:
   - Name: `Test Product - Priority`
   - API SKU: `TEST-PRIORITY-001`
   - Supplier Company Code: `TEST001`
   - Price Group: `STANDARD` (rate 0.80)
   - Manufacturer: `Thermo Fisher` (rate 0.75)
   - Fixed Purchase Price: `6000`
   - API List Price: `10000`
2. Save

**Expected Result:**
- Supplier Info price = `6000` (fixed price wins)

**Steps 2:**
3. Remove Fixed Purchase Price (set to 0)
4. Click "Reprocess" button

**Expected Result:**
- Supplier Info price = `8000` (price group rate wins)

**Steps 3:**
5. Remove Price Group (set to blank)
6. Click "Reprocess" button

**Expected Result:**
- Supplier Info price = `7500` (manufacturer rate wins)

---

### Test 8: Sales Order - Automatic Discount (Price Group)

**Objective**: Verify automatic discount application on sales

**Steps:**
1. Use product from Test 5 (TEST-PG-001, price group rate 0.80 = 20% discount)
2. Navigate to Sales > Orders > Quotations
3. Create new quotation:
   - Customer: Select any customer
   - Add order line:
     - Product: `Test Product - Price Group`
     - Quantity: `10`
4. Observe discount field

**Expected Result:**
- Discount field automatically populated with `20.00`
- Applied Rate Source: `Price Group Rate`
- Applied Rate Value: `0.8000`
- Unit Price: `10000` (from list_price)
- Subtotal: `8000` per unit (after 20% discount)

**Validation:**
```python
so = env['sale.order'].search([...], limit=1, order='id desc')
line = so.order_line[0]
print(f"Discount: {line.discount}%")  # Should be 20.0
print(f"Source: {line.applied_rate_source}")  # Should be 'price_group'
print(f"Rate: {line.applied_rate_value}")  # Should be 0.8
```

---

### Test 9: Sales Order - Automatic Discount (Manufacturer)

**Objective**: Verify manufacturer discount when price group is not set

**Steps:**
1. Use product from Test 6 (TEST-MK-001, manufacturer rate 0.75 = 25% discount)
2. Create new quotation
3. Add product to order line

**Expected Result:**
- Discount: `25.00%`
- Applied Rate Source: `Manufacturer Rate`
- Applied Rate Value: `0.7500`

---

### Test 10: Sales Order - Manual Discount Override

**Objective**: Verify manual discount override is tracked

**Steps:**
1. Create quotation with product that has automatic discount
2. Manually change discount from `20.00` to `30.00`
3. Save

**Expected Result:**
- Discount: `30.00%`
- Applied Rate Source: `manual`
- Applied Rate Value: `False`

---

### Test 11: Sales Order - Reapply Automatic Discounts

**Objective**: Verify bulk discount reapplication

**Steps:**
1. Create quotation with multiple products (some with auto discounts)
2. Manually change all discounts to `0`
3. Click **Reapply Auto Discounts** button in quotation header

**Expected Result:**
- All automatic discounts reapplied
- Products with rate masters get their discounts back
- Products without rate masters remain at 0%
- Notification: "Automatic discounts reapplied to all order lines"

---

### Test 12: Product Manual Reprocess

**Objective**: Verify manual reprocessing button works

**Steps:**
1. Open any product with external API data
2. Change supplier code
3. Click **Reprocess** button

**Expected Result:**
- Auto Process Status changes to `Processing` then `Success`
- Vendor re-identified (if mapping exists)
- Purchase price recalculated
- Supplier info updated
- Status message updated
- Notification: "Product(s) reprocessed successfully"

---

### Test 13: Route Assignment Verification

**Objective**: Verify Buy and MTO routes are assigned

**Steps:**
1. Create product as in Test 5
2. Navigate to product > Inventory tab
3. Check Routes field

**Expected Result:**
- "Buy" route present
- "Make To Order" route present (requires OCA module)

**Validation:**
```python
product = env['product.template'].search([('api_sku', '=', 'TEST-PG-001')])
route_names = [r.name for r in product.route_ids]
print(f"Routes: {route_names}")
assert 'Buy' in str(route_names) or 'buy' in str(route_names).lower()
assert 'MTO' in str(route_names) or 'Make To Order' in str(route_names)
```

---

### Test 14: Error Handling - No Vendor Mapping

**Objective**: Verify graceful handling when vendor mapping is missing

**Steps:**
1. Create product with:
   - Supplier Company Code: `NONEXISTENT`
   - Other fields populated
2. Save

**Expected Result:**
- Auto Process Status: `Success` (doesn't fail)
- Message contains: "Vendor not identified for supplier code: NONEXISTENT"
- No supplier info created
- Routes still assigned

---

### Test 15: Error Handling - Invalid Rate

**Objective**: Verify rate validation

**Steps:**
1. Try to create price group rate with rate `2.5` (exceeds max)
2. Save

**Expected Result:**
- Validation error: "Rate must be between 0.0 and 2.0"
- Record not saved

**Steps 2:**
1. Try rate `-0.5` (negative)
2. Save

**Expected Result:**
- Same validation error
- Record not saved

---

### Test 16: Date Validity - Expired Rate

**Objective**: Verify expired rates are not used

**Steps:**
1. Create price group rate:
   - Supplier Code: `TEST001`
   - Group Name: `EXPIRED`
   - Rate: `0.50`
   - Valid From: `2020-01-01`
   - Valid To: `2020-12-31` (past date)
   - Active: ✓
2. Create product with price group `EXPIRED`
3. Save

**Expected Result:**
- Rate not applied (expired)
- Fallback to list_price × 1.0
- Log warning: "Price group rate expired: TEST001/EXPIRED"

---

### Test 17: Date Validity - Future Rate

**Objective**: Verify future rates are not used yet

**Steps:**
1. Create price group rate:
   - Valid From: `2030-01-01` (future date)
   - Valid To: `2030-12-31`
   - Rate: `0.50`
2. Create product with this price group
3. Save

**Expected Result:**
- Rate not applied (not yet valid)
- Fallback to list_price × 1.0
- Log warning: "Price group rate not yet valid"

---

### Test 18: Supplier Info Upsert

**Objective**: Verify update vs create behavior

**Steps:**
1. Create product (creates supplier info)
2. Note supplier info price
3. Update product's `purchase_price_fixed` to new value
4. Save (or click Reprocess)

**Expected Result:**
- Same supplier info record updated (not duplicate created)
- Price updated to new value
- Only one supplier info record exists for product+vendor

**Validation:**
```python
product = env['product.template'].search([...])
supplierinfo_count = env['product.supplierinfo'].search_count([
    ('product_tmpl_id', '=', product.id)
])
assert supplierinfo_count == 1, f"Expected 1, found {supplierinfo_count}"
```

---

### Test 19: Multiple Products Bulk Import

**Objective**: Test performance with multiple products

**Steps:**
1. Create 100+ products programmatically:
```python
for i in range(100):
    env['product.template'].create({
        'name': f'Bulk Test Product {i}',
        'api_sku': f'BULK-{i:04d}',
        'api_supplier_comp_code': 'TEST001',
        'api_price_group': 'STANDARD',
        'api_list_price': 1000.0 + i,
        'list_price': 1000.0 + i,
    })
```

**Expected Result:**
- All products processed successfully
- All have supplier info with correct prices
- No database errors
- Reasonable processing time (< 1 second per product)

---

### Test 20: Sales Order Line - Programmatic Creation

**Objective**: Verify discount applies when creating lines via API/code

**Steps:**
```python
so = env['sale.order'].create({'partner_id': customer_id})
line = env['sale.order.line'].create({
    'order_id': so.id,
    'product_id': product_id,  # Product with auto discount
    'product_uom_qty': 5,
})
```

**Expected Result:**
- Discount automatically applied even in programmatic creation
- Applied rate source populated

---

## Test Report Template

Use this template to document test results:

```
### Test X: [Test Name]
Date: YYYY-MM-DD
Tester: [Name]
Odoo Version: 18.0
Module Version: 18.0.1.0.0

**Status**: ✅ PASS / ❌ FAIL / ⚠️ PARTIAL

**Notes**:
- [Any observations]
- [Any issues found]
- [Screenshots if applicable]

**Actual Results**:
[What actually happened]

**Deviations from Expected**:
[Any differences]
```

## Automated Testing (Optional)

For automated testing, create test cases:

```python
# tests/__init__.py
from . import test_supplier_mapping
from . import test_rate_masters
from . import test_product_processing
from . import test_sales_discount

# tests/test_sales_discount.py
from odoo.tests.common import TransactionCase

class TestSalesDiscount(TransactionCase):
    
    def setUp(self):
        super().setUp()
        # Setup test data
        
    def test_price_group_discount(self):
        """Test automatic price group discount application"""
        # Create rate master
        # Create product
        # Create sale order line
        # Assert discount applied
        pass
```

Run tests:
```bash
odoo-bin -c odoo.conf -d test_db -i product_auto_route_supplier --test-enable --stop-after-init
```

## Performance Testing

### Benchmark Targets

- Product creation with auto-processing: < 1 second per product
- Vendor lookup: < 0.1 seconds
- Rate lookup: < 0.1 seconds
- Sale order line discount application: < 0.2 seconds

### Load Testing

Test with:
- 1,000 products
- 100 vendor mappings
- 500 rate master records
- 50 concurrent sale orders

All operations should complete within performance targets.
