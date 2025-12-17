# Quick Start Guide - DOG API Integration

আপনার Odoo 18 তে DOG API Integration module দ্রুত setup করার জন্য এই guide follow করুন।

## 🚀 দ্রুত শুরু করুন (Bangla)

### ১. Module Install করুন

```bash
# Module folder কপি করুন
cp -r dog_api_integration /path/to/odoo/addons/

# Odoo restart করুন
sudo systemctl restart odoo
```

### ২. Odoo তে Install করুন

1. **Apps** > **Update Apps List** click করুন
2. "DOG API Integration" search করুন
3. **Install** button click করুন

### ৩. Partner Setup (সবচেয়ে গুরুত্বপূর্ণ!)

#### Supplier Setup:
```
Purchase > Configuration > Suppliers
- Reference (ref): SUP001, SUP002 etc. ✅ REQUIRED
- Name: Supplier এর নাম ✅ REQUIRED
```

#### Company Setup:
```
Settings > Companies > Your Company > Update Info
- Reference (ref): COMP001 etc. ✅ REQUIRED
```

#### Customer Setup (Direct Shipment এর জন্য):
```
Contacts > Customer
- Reference (ref): CUST001 etc. ✅ REQUIRED
- ZIP/Postal Code ✅ REQUIRED
- City ✅ REQUIRED
- Street ✅ REQUIRED
```

### ৪. Product Setup

```
Purchase > Products > Products
- Internal Reference: PROD-001, PROD-002 etc. ✅ REQUIRED
```

### ৫. Test Order তৈরি করুন

1. **Purchase > Orders > Purchase Orders** > **Create**
2. Supplier select করুন (ref থাকতে হবে)
3. **Delivery Mode** select করুন:
   - **Company Delivery** (নিজের warehouse এ)
   - **Direct Shipment** (সরাসরি customer এর কাছে)
4. Product add করুন (default_code থাকতে হবে)
5. **Confirm Order** click করুন

### ৬. Status Check করুন

Order confirm করার পর:
- **DOG Integration** tab open করুন
- **Exported to DOG**: ✓ Checked হবে
- **DOG Export Status**: Success দেখাবে
- **DOG Export Message**: API response দেখাবে

---

## 🇬🇧 Quick Start (English)

### 1. Install Module

```bash
# Copy module folder
cp -r dog_api_integration /path/to/odoo/addons/

# Restart Odoo
sudo systemctl restart odoo
```

### 2. Install in Odoo

1. Go to **Apps** > **Update Apps List**
2. Search "DOG API Integration"
3. Click **Install**

### 3. Partner Setup (Most Important!)

#### Suppliers:
- Reference (ref): **REQUIRED** (e.g., SUP001)
- Name: **REQUIRED**

#### Company:
- Partner Reference (ref): **REQUIRED** (e.g., COMP001)

#### Customers (for Direct Shipment):
- Reference (ref): **REQUIRED**
- ZIP, City, Street: **REQUIRED**

### 4. Product Setup

- Internal Reference (default_code): **REQUIRED**

### 5. Create Test Order

1. Create Purchase Order
2. Select Supplier (must have ref)
3. Choose Delivery Mode
4. Add Products (must have default_code)
5. Confirm Order → Auto sends to DOG API!

### 6. Check Status

After confirmation:
- Open **DOG Integration** tab
- Check export status, date, and message

---

## 📋 Field Requirements Checklist

### Required for ALL Orders:
- ✅ Supplier Reference (ref)
- ✅ Company Partner Reference (ref)
- ✅ Product Internal Reference (default_code)
- ✅ Order Date
- ✅ Product Quantity
- ✅ Unit Price

### Additional for Direct Shipment:
- ✅ Ship to Partner Reference (ref)
- ✅ Ship to ZIP Code
- ✅ Ship to City
- ✅ Ship to Street

---

## 🔧 Manual Resend

যদি কোন order send fail করে:

1. Purchase Order open করুন
2. **Send to DOG API** button click করুন (header এ)
3. Status check করুন **DOG Integration** tab এ

---

## 🐛 Common Issues & Solutions

### Issue 1: Export Failed - "Missing supplier_code"
**Solution:** Supplier এর Reference (ref) field fill করুন

### Issue 2: Export Failed - "Missing buyer_code"
**Solution:** Company Partner এর Reference (ref) field fill করুন

### Issue 3: Export Failed - "Missing item_code"
**Solution:** Product এর Internal Reference (default_code) fill করুন

### Issue 4: Button দেখা যাচ্ছে না
**Solution:** আগে Order confirm করতে হবে

---

## 📊 API Format Example

API তে এই format এ data যায়:

```json
{
  "data": [
    {
      "po_number": "PO00045",
      "po_line_number": 10,
      "order_date": "2024-12-16",
      "supplier_code": "SUP001",
      "supplier_name": "ABC Company",
      "item_code": "PROD-001",
      "item_name": "Product A",
      "ordered_qty": 10.0,
      "unit_price": 1500.0,
      "line_amount": 15000.0,
      ...
    }
  ]
}
```

---

## 🔍 Verify Everything Works

```bash
# Odoo logs check করুন
tail -f /var/log/odoo/odoo-server.log | grep "DOG API"

# API independently test করুন
python dog_api_integration/test_dog_api.py
```

---

## 📞 Support

- **Developer**: Md Abu Sayed
- **Company**: SAGBRAIN CORPORATION
- **Email**: support@sagbrain.com

---

## 📚 Full Documentation

বিস্তারিত জানতে দেখুন:
- **README.md** - Complete feature list
- **INSTALLATION.md** - Detailed installation guide
- **CHANGELOG.md** - Version history

---

**Happy Integrating! 🎉**
