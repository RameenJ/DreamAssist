#!/usr/bin/env python
"""Test backend imports to diagnose issues"""

import sys
import traceback

def test_import(module_name, path=None):
    try:
        if path:
            sys.path.insert(0, path)
        __import__(module_name)
        print(f"✅ {module_name} imported successfully")
        return True
    except Exception as e:
        print(f"❌ {module_name} import failed:")
        traceback.print_exc()
        print()
        return False

# Test individual services first
print("Testing individual services...")
test_import("services.ai_service")
test_import("services.sentiment_analysis_service")
test_import("services.vector_service")

# Then test main
print("\nTesting main module...")
if test_import("main"):
    print("\n✅ All imports successful! Backend can start.")
else:
    print("\n❌ Backend import failed. Check errors above.")
