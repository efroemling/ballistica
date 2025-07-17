#!/usr/bin/env python3
"""
Test script to check if registration system can be imported
"""

import sys
sys.path.append('/home/heyfang/ballistica/src/assets/ba_data/python')

print("Testing registration system import...")

try:
    print("1. Testing direct import...")
    from bautils.tourny.register import get_global_database, is_registrations_enabled
    print("✅ Direct import successful")
    
    print("2. Testing function calls...")
    print(f"   - is_registrations_enabled(): {is_registrations_enabled()}")
    print(f"   - get_global_database(): {get_global_database()}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")

print("\nChecking file exists...")
import os
register_file = '/home/heyfang/ballistica/src/assets/ba_data/python/bautils/tourny/register.py'
print(f"File exists: {os.path.exists(register_file)}")

if os.path.exists(register_file):
    with open(register_file, 'r') as f:
        content = f.read()
        print(f"File size: {len(content)} characters")
        if 'def get_global_database' in content:
            print("✅ get_global_database function found")
        else:
            print("❌ get_global_database function not found")
