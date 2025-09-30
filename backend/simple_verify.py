#!/usr/bin/env python3
"""
Simple Import Verification Script

Tests that basic imports work without external dependencies.
"""

import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🔍 Verifying basic imports...")

# Test basic imports that don't require external dependencies
basic_tests = [
    ('sys', 'import sys'),
    ('os', 'import os'),
    ('json', 'import json'),
    ('datetime', 'from datetime import datetime'),
]

for test_name, test_code in basic_tests:
    try:
        exec(test_code)
        print(f"✅ {test_name}")
    except Exception as e:
        print(f"❌ {test_name}: {e}")

print("\n🔍 Testing module structure...")

# Test that our fixed modules can be imported (without external deps)
module_tests = [
    'app.core.config',
    'app.utils.logging',
    'app.models.mission',
    'app.models.drone',
    'app.models.discovery',
]

for module in module_tests:
    try:
        # Try to import just the module structure
        parts = module.split('.')
        module_path = '.'.join(parts[:-1])
        attr_name = parts[-1]

        exec(f"import {module_path}")
        module_obj = eval(module_path)
        if hasattr(module_obj, attr_name):
            print(f"✅ {module} (attribute exists)")
        else:
            print(f"⚠️ {module} (module imported but attribute missing)")

    except Exception as e:
        print(f"❌ {module}: {e}")

print("\n📊 Import verification complete!")
print("Note: External dependencies (FastAPI, SQLAlchemy, etc.) need to be installed for full functionality.")