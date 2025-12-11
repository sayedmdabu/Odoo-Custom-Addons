# Monthly Billing Module for Odoo 18

## Overview

This module implements Japanese-style closing date-based monthly billing (まとめ請求) for Odoo 18 Community Edition and Enterprise Edition.

## Features

- **Monthly Invoice Aggregation**: Aggregate customer invoices by closing period and customer
- **Flexible Closing Dates**: Support for end-of-month closing, 20th, 15th, 10th, or custom closing days
- **Period Calculation**: Automatic calculation of billing periods based on closing logic
- **Professional PDF Reports**: Generate professional Japanese-style billing statements
- **Multi-company Support**: Full support for multi-company environments
- **Internationalization**: Full i18n support (Japanese and English)
- **State Management**: Draft → Confirmed → Done workflow with cancellation support
- **Preview Mode**: Preview target invoices before generating monthly billings

## Installation

1. Copy the `monthly_billing` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the module from Apps menu

## Configuration

### Customer Setup

Navigate to Contacts and configure monthly billing settings for each customer:

- **Closing Day**: Set the closing day (1-31, where 31 = end of month)
- **Closing Type**: Select from predefined types or custom
- **Billing Group Code**: Optional code for group billing

### User Groups

The module creates two user groups:

- **Monthly Billing User**: Can view and use monthly billing features
- **Monthly Billing Manager**: Full access including create, edit, and delete

## Usage

### Generating Monthly Billings

1. Navigate to **Invoicing → Monthly Billing → Generate Monthly Billing**
2. Specify the closing year/month (format: YYYY-MM, e.g., 2025-10)
3. Specify the closing day (1-31)
4. (Optional) Select target customers (leave empty for all customers)
5. Select invoice state filter (Posted Only or Posted and Draft)
6. Click **Preview** to see estimated results
7. Click **Generate Monthly Billing** to create records

### Closing Period Logic

#### End-of-Month Closing (Day 31)
- **Period**: From 1st to last day of the specified month
- **Example**: 2025-10 with day 31 = 2025-10-01 to 2025-10-31

#### Specific Day Closing (Day < 31)
- **Period**: From (previous month's closing day + 1) to current month's closing day
- **Example**: 2025-10 with day 20 = 2025-09-21 to 2025-10-20

### Managing Monthly Billings

1. Navigate to **Invoicing → Monthly Billing → Monthly Billings**
2. View list of all monthly billings
3. Click on a record to view details
4. Use action buttons to:
   - **Confirm**: Confirm the billing (draft → confirmed)
   - **Done**: Finalize the billing (confirmed → done)
   - **Cancel**: Cancel the billing
   - **Print PDF**: Generate and download the billing statement

### PDF Report

The module generates professional Japanese-style billing statements including:

- Company and customer information
- Billing period details
- Amount summary (untaxed, tax, total)
- Detailed line items with original invoice references
- Payment information
- Contact information
- Bilingual headers (English/Japanese)

## Technical Details

### Models

#### monthly.billing.header
Main model for monthly billing statements

#### monthly.billing.line
Detail lines aggregated from invoice lines

#### monthly.billing.generate.wizard
Transient model for generation wizard

### Views

- Tree view with search filters and grouping
- Form view with tabs and action buttons
- Wizard view for generation

### Reports

- QWeb-based PDF report with professional layout
- Bilingual support (Japanese/English)

### Security

- Access control based on user groups
- Multi-company record rules
- State-based field restrictions

## Requirements

- Odoo 18 Community Edition or Enterprise Edition
- Python 3.10+
- Dependencies: base, account, contacts

## Performance

- Batch creation for invoice lines (optimized for large volumes)
- Efficient search with indexed fields
- Computed fields with proper storage

## Compatibility

- **Odoo Version**: 18.0
- **Edition**: Community Edition (CE) and Enterprise Edition (EE)
- **Database**: PostgreSQL

## Support

For issues, questions, or feature requests, please contact your system administrator or the module developer.

## License

LGPL-3

## Credits

Developed for Odoo 18 Community Edition
Supports Japanese business practices for monthly billing

---

## 日本語版

このモジュールは日本の商習慣に基づく月次請求(まとめ請求)機能を提供します。

### 主な機能

- 締日ベースの月次請求書作成
- 柔軟な締日設定（月末締、20日締など）
- プロフェッショナルなPDF請求書
- マルチカンパニー対応
- 日本語・英語対応

### 締めロジック

- **月末締（31日）**: 当月1日〜当月末日
- **特定日締（20日など）**: 前月締日+1日〜当月締日

詳細は英語版ドキュメントをご参照ください。
