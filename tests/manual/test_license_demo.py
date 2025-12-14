#!/usr/bin/env python3
"""
Manual test to demonstrate the license system behavior.

Run this script to see how the license system blocks ChatGPT imports
and allows other formats without a license.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from db.licensing import LicenseManager
from db.importers.errors import LicenseRequiredError


def test_license_manager():
    """Test basic license manager functionality."""
    print("=" * 60)
    print("TESTING LICENSE MANAGER")
    print("=" * 60)
    
    # Test without license
    print("\n1. Testing without license key:")
    mgr = LicenseManager()
    print(f"   Has ChatGPT feature: {mgr.has_feature('chatgpt_importer')}")
    print(f"   Enabled features: {mgr.get_enabled_features()}")
    
    # Test with invalid license
    print("\n2. Testing with invalid license key:")
    mgr = LicenseManager(license_key="INVALID-KEY")
    print(f"   Has ChatGPT feature: {mgr.has_feature('chatgpt_importer')}")
    
    # Test with valid Pro license
    print("\n3. Testing with valid Pro license:")
    mgr = LicenseManager(license_key="DOVOS-PRO-demo123")
    print(f"   Has ChatGPT feature: {mgr.has_feature('chatgpt_importer')}")
    print(f"   Has DOCX feature: {mgr.has_feature('docx_importer')}")
    print(f"   Enabled features: {mgr.get_enabled_features()}")
    
    # Test with valid Enterprise license
    print("\n4. Testing with valid Enterprise license:")
    mgr = LicenseManager(license_key="DOVOS-ENT-demo456")
    print(f"   Has ChatGPT feature: {mgr.has_feature('chatgpt_importer')}")
    
    # Test license status
    print("\n5. License status without license:")
    mgr = LicenseManager()
    status = mgr.get_license_status()
    print(f"   Has license: {status['has_license']}")
    print(f"   Enabled features: {status['enabled_features']}")
    print(f"   Missing features: {status['missing_features']}")
    print(f"   Feature names: {list(status['feature_names'].values())}")


def test_license_error():
    """Test the license error message."""
    print("\n" + "=" * 60)
    print("TESTING LICENSE ERROR MESSAGE")
    print("=" * 60)
    
    error = LicenseRequiredError(
        feature_name='chatgpt_importer',
        format_name='ChatGPT'
    )
    
    print("\nError message shown to users:")
    print("-" * 60)
    print(error.message)
    print("-" * 60)


def test_import_blocking():
    """Test that imports are blocked without license."""
    print("\n" + "=" * 60)
    print("TESTING IMPORT BLOCKING")
    print("=" * 60)
    
    from db.services.import_service import ConversationImportService
    
    # Create a sample ChatGPT conversation
    chatgpt_data = [{
        'title': 'Demo Conversation',
        'create_time': 1234567890,
        'update_time': 1234567890,
        'mapping': {
            'node1': {
                'message': {
                    'author': {'role': 'user'},
                    'content': {'parts': ['Hello, this is a test']}
                },
                'create_time': 1234567890
            }
        }
    }]
    
    print("\n1. Attempting to import ChatGPT conversation WITHOUT license:")
    service = ConversationImportService()
    try:
        service.import_json_data(chatgpt_data)
        print("   ❌ Import succeeded (should have failed!)")
    except ValueError as e:
        print("   ✅ Import blocked as expected")
        print(f"   Error message: {str(e)[:100]}...")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DOVOS LICENSE SYSTEM - MANUAL TEST DEMO")
    print("=" * 60)
    
    test_license_manager()
    test_license_error()
    test_import_blocking()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nTo enable ChatGPT imports, set one of:")
    print("  1. Environment variable: DOVOS_LICENSE_KEY=DOVOS-PRO-your-key")
    print("  2. Database setting via /settings page")
    print()
