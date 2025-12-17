#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DOG API Test Script

This script can be used to test the DOG API independently of Odoo.
Useful for debugging and understanding the API structure.

Usage:
    python test_dog_api.py
"""

import requests
import json
from datetime import datetime

# API Configuration
API_URL = "https://stage.scm-bio.net/api/odoo/create/index.php"
API_USERNAME = "odoo"
API_PASSWORD = "oaJE2@5V"

# Base64 encoded credentials: "odoo:oaJE2@5V"
AUTH_HEADER = "Basic b2RvbzpvYUpFMkA1Vg=="


def create_test_data():
    """Create sample test data according to DOG specification"""
    
    test_data = [
        {
            # Header Information
            "po_number": "PO00123",
            "po_line_number": 10,
            "order_date": "2024-12-16",
            "requested_date": "2024-12-25",
            
            # Buyer (Company) Information
            "buyer_code": "COMP001",
            "buyer_name": "Test Company Ltd.",
            
            # Supplier Information
            "supplier_code": "SUP001",
            "supplier_name": "Test Supplier Co.",
            "supplier_quote_number": "QT-2024-001",
            
            # Delivery Information
            "delivery_destination_type": "2",  # Direct shipment
            "ship_to_party_code": "CUST001",
            "ship_to_party_name": "Test Customer University",
            "ship_to_zip": "100-0001",
            "ship_to_state": "Tokyo",
            "ship_to_city": "Chiyoda-ku",
            "ship_to_street": "1-1-1 Chiyoda Building 3F",
            "ship_to_phone": "03-1234-5678",
            
            # Product Information
            "item_code": "PROD-001",
            "item_name": "Test Product A",
            "ordered_qty": 10.0,
            "unit_price": 1500.0,
            "line_amount": 15000.0,
            
            # Remarks
            "po_remark": "Test order header remark",
            "line_remark": "Test line remark"
        },
        {
            # Second line
            "po_number": "PO00123",
            "po_line_number": 20,
            "order_date": "2024-12-16",
            "requested_date": "2024-12-25",
            
            "buyer_code": "COMP001",
            "buyer_name": "Test Company Ltd.",
            
            "supplier_code": "SUP001",
            "supplier_name": "Test Supplier Co.",
            "supplier_quote_number": "QT-2024-001",
            
            "delivery_destination_type": "2",
            "ship_to_party_code": "CUST001",
            "ship_to_party_name": "Test Customer University",
            "ship_to_zip": "100-0001",
            "ship_to_state": "Tokyo",
            "ship_to_city": "Chiyoda-ku",
            "ship_to_street": "1-1-1 Chiyoda Building 3F",
            "ship_to_phone": "03-1234-5678",
            
            "item_code": "PROD-002",
            "item_name": "Test Product B",
            "ordered_qty": 5.0,
            "unit_price": 2500.0,
            "line_amount": 12500.0,
            
            "po_remark": "Test order header remark",
            "line_remark": "Different package"
        }
    ]
    
    return test_data


def send_to_dog_api(data):
    """Send data to DOG API"""
    
    payload = json.dumps({
        "data": data
    }, indent=2)
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': AUTH_HEADER
    }
    
    print("=" * 80)
    print("SENDING REQUEST TO DOG API")
    print("=" * 80)
    print(f"\nURL: {API_URL}")
    print(f"\nHeaders:")
    print(json.dumps(headers, indent=2))
    print(f"\nPayload:")
    print(payload)
    print("\n" + "=" * 80)
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            data=payload,
            timeout=30
        )
        
        print("\nRESPONSE RECEIVED")
        print("=" * 80)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(response.text)
        print("=" * 80)
        
        # Check if request was successful
        response.raise_for_status()
        
        return {
            'success': True,
            'status_code': response.status_code,
            'response': response.text
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f"\nResponse: {e.response.text}"
        
        print("\nERROR OCCURRED")
        print("=" * 80)
        print(error_msg)
        print("=" * 80)
        
        return {
            'success': False,
            'error': error_msg
        }


def validate_data(data):
    """Validate test data has all required fields"""
    
    required_fields = [
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
    
    print("\nVALIDATING DATA")
    print("=" * 80)
    
    for idx, record in enumerate(data):
        print(f"\nRecord {idx + 1}:")
        missing_fields = []
        
        for field in required_fields:
            if field not in record or not record[field]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"  ❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        else:
            print(f"  ✓ All required fields present")
    
    print("\n✓ Validation passed!")
    print("=" * 80)
    return True


def main():
    """Main function"""
    
    print("\n" + "=" * 80)
    print("DOG API TEST SCRIPT")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}")
    print("=" * 80)
    
    # Create test data
    test_data = create_test_data()
    
    # Validate data
    if not validate_data(test_data):
        print("\n❌ Validation failed. Please check your test data.")
        return
    
    # Ask for confirmation
    print("\n" + "=" * 80)
    response = input("Do you want to send this test data to DOG API? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Test cancelled.")
        return
    
    # Send to API
    result = send_to_dog_api(test_data)
    
    # Print result
    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    
    if result['success']:
        print("✓ SUCCESS: Data sent successfully to DOG API")
        print(f"  Status Code: {result['status_code']}")
        print(f"  Response: {result['response']}")
    else:
        print("❌ FAILED: Could not send data to DOG API")
        print(f"  Error: {result['error']}")
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
