# -*- coding: utf-8 -*-

"""
DOG API Integration - Additional Configuration and Helper Notes

This file contains additional configuration options and helper functions
that can be customized based on specific requirements.
"""

# ==============================================================================
# API CONFIGURATION
# ==============================================================================

# Production API Endpoint (update when moving to production)
PRODUCTION_API_URL = "https://production.scm-bio.net/api/odoo/create/index.php"

# Staging API Endpoint (current)
STAGING_API_URL = "https://stage.scm-bio.net/api/odoo/create/index.php"

# API Timeout (seconds)
API_TIMEOUT = 30

# ==============================================================================
# FIELD MAPPING CUSTOMIZATION
# ==============================================================================

# If you need to customize field mappings, you can modify the 
# _prepare_dog_api_data method in models/purchase_order.py

# Example custom field mappings:
CUSTOM_FIELD_MAPPINGS = {
    # 'dog_field_name': 'odoo_field_path',
    # Example:
    # 'custom_buyer_code': 'company_id.x_custom_code',
    # 'custom_supplier_code': 'partner_id.x_supplier_custom_code',
}

# ==============================================================================
# DELIVERY MODE CONFIGURATION
# ==============================================================================

# Delivery mode mapping
DELIVERY_MODE_MAPPING = {
    'company': '1',           # 自社 (Company delivery)
    'customer_drop_ship': '2' # 直送 (Direct shipment)
}

# ==============================================================================
# LANGUAGE SETTINGS
# ==============================================================================

# Default language for product names
DEFAULT_PRODUCT_LANG = 'ja_JP'  # Japanese

# Fallback languages if Japanese not available
FALLBACK_LANGUAGES = ['en_US', 'ja_JP']

# ==============================================================================
# ERROR HANDLING
# ==============================================================================

# Retry configuration (if you want to implement retry logic)
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

# Log level for DOG API operations
# Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
DOG_LOG_LEVEL = 'INFO'

# Enable detailed API request/response logging
DETAILED_API_LOGGING = True

# ==============================================================================
# DATA VALIDATION RULES
# ==============================================================================

# Required fields that must be present before sending to API
REQUIRED_FIELDS = [
    'po_number',
    'po_line_number', 
    'order_date',
    'buyer_code',
    'buyer_name',
    'supplier_code',
    'supplier_name',
    'delivery_destination_type',
    'ship_to_party_code',
    'ship_to_party_name',
    'item_code',
    'item_name',
    'ordered_qty',
    'unit_price',
    'line_amount',
]

# Fields required only for direct shipment (delivery_destination_type = '2')
DIRECT_SHIP_REQUIRED_FIELDS = [
    'ship_to_zip',
    'ship_to_state',
    'ship_to_city',
    'ship_to_street',
]

# ==============================================================================
# NUMBER FORMATTING
# ==============================================================================

# Decimal places for quantity
QTY_DECIMAL_PLACES = 3

# Decimal places for unit price
PRICE_DECIMAL_PLACES = 4

# Decimal places for line amount
AMOUNT_DECIMAL_PLACES = 2

# ==============================================================================
# DATE/TIME FORMATTING
# ==============================================================================

# Date format for API (YYYY-MM-DD or YYYY/MM/DD)
API_DATE_FORMAT = '%Y-%m-%d'  # Can be changed to '%Y/%m/%d' if needed

# Timezone for date conversion
DEFAULT_TIMEZONE = 'Asia/Tokyo'

# ==============================================================================
# BATCH PROCESSING (if needed for bulk exports)
# ==============================================================================

# Maximum records per API batch
MAX_BATCH_SIZE = 100

# Enable batch mode
ENABLE_BATCH_PROCESSING = False

# ==============================================================================
# TESTING & DEVELOPMENT
# ==============================================================================

# Enable test mode (will log but not actually send to API)
TEST_MODE = False

# Mock API response for testing
MOCK_API_RESPONSE = {
    'status': 'success',
    'message': 'Data received successfully',
    'records_processed': 0
}

# ==============================================================================
# CUSTOM HOOKS
# ==============================================================================

# You can define custom pre/post processing functions here
# and call them from the main model

def pre_send_hook(order, data_list):
    """
    Custom function to run before sending data to API
    
    Args:
        order: purchase.order recordset
        data_list: list of dictionaries to be sent to API
    
    Returns:
        Modified data_list or raises exception to stop processing
    """
    # Example: Add custom validation
    # for data in data_list:
    #     if not data.get('item_code'):
    #         raise ValueError('Item code is required')
    
    return data_list


def post_send_hook(order, response):
    """
    Custom function to run after successful API send
    
    Args:
        order: purchase.order recordset
        response: API response text
    """
    # Example: Send notification email
    # order.message_post(
    #     body=f"Successfully exported to DOG API. Response: {response}",
    #     subject="DOG Export Success"
    # )
    pass


# ==============================================================================
# NOTES FOR IMPLEMENTATION
# ==============================================================================

"""
IMPLEMENTATION CHECKLIST:

1. Partner Setup (res.partner):
   □ Add 'ref' (Reference/Code) for all suppliers
   □ Add 'ref' for company partner
   □ Add 'ref' for customer/ship-to partners
   □ Verify address fields are complete

2. Company Setup (res.company):
   □ Ensure company has linked partner_id
   □ Verify company partner has 'ref' field filled

3. Product Setup (product.product):
   □ Add 'default_code' (Internal Reference) for all products
   □ Add Japanese translations if needed
   □ Verify product names are set

4. Purchase Order Setup:
   □ Select appropriate Delivery Mode
   □ For Direct Shipment: Select Ship to Partner
   □ Fill Supplier Quote Number if available
   □ Add order notes if needed

5. Testing:
   □ Create test purchase order
   □ Fill all required fields
   □ Confirm order and check DOG Integration tab
   □ Verify API logs
   □ Check DOG system for received data

6. Production Deployment:
   □ Update API URL if different
   □ Update credentials if needed
   □ Enable proper logging
   □ Set up monitoring/alerts
   □ Train users on proper usage
"""
