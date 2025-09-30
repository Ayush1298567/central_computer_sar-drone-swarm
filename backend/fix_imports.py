#!/usr/bin/env python3
"""
Universal Import Fixer Script for SAR Drone System

This script fixes relative import issues across all modules by:
1. Detecting relative imports in Python files
2. Converting them to absolute imports with proper path setup
3. Ensuring all modules can import each other correctly

Usage: python3 backend/fix_imports.py
"""

import os
import sys
import ast
import re
import glob
from pathlib import Path

def find_python_files(directory):
    """Find all Python files in the given directory recursively."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    return python_files

def detect_relative_imports(content):
    """Detect relative imports in file content."""
    relative_imports = []

    # Pattern to match relative imports like: from ..xxx import yyy or from app.xxx import yyy
    pattern = r'from\s+(\.\..*?|app\.[^\s]+)\s+import\s+(.+)'

    lines = content.split('\n')
    for i, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            module_path = match.group(1)
            imports = match.group(2)
            relative_imports.append({
                'line_number': i + 1,
                'original_line': line,
                'module_path': module_path,
                'imports': imports
            })

    return relative_imports

def fix_relative_imports(content, file_path):
    """Fix relative imports in file content."""
    lines = content.split('\n')
    modified = False

    # Pattern to match: from ..xxx import yyy or from app.xxx import yyy
    pattern = r'from\s+(\.\..*?|app\.[^\s]+)\s+import\s+(.+)'

    for i, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            full_import_path = match.group(1)
            imports = match.group(2)

            # Skip if already has path setup above
            if i > 0 and 'sys.path.insert' in lines[i-1]:
                continue

            # Handle different types of imports
            if full_import_path.startswith('..'):
                # Relative import - convert to absolute
                # Count the number of .. to determine the module path
                dot_count = len(full_import_path) - len(full_import_path.lstrip('.'))
                module_path = full_import_path[dot_count:]  # Remove the .. prefix

                replacement = f'''import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app{module_path} import {imports}'''
            else:
                # Absolute import from app
                module_path = full_import_path[4:]  # Remove 'app.' prefix

                replacement = f'''import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.{module_path} import {imports}'''

            lines[i] = replacement
            modified = True
            print(f"  🔧 Fixed import in {file_path}:{i+1}: {full_import_path}")

    return '\n'.join(lines), modified

def process_file(file_path):
    """Process a single file to fix relative imports."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if file doesn't contain relative or absolute imports
        if 'from app.' not in content and 'from ..' not in content:
            return False

        # Detect relative imports
        relative_imports = detect_relative_imports(content)
        if not relative_imports:
            return False

        print(f"\n📄 Processing {file_path}")
        print(f"  Found {len(relative_imports)} relative imports")

        # Fix the imports
        fixed_content, modified = fix_relative_imports(content, file_path)

        if modified:
            # Create backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

            print(f"  ✅ Fixed {len(relative_imports)} imports, backup created: {backup_path}")
            return True
        else:
            print("  ⚠️ No imports needed fixing")
            return False

    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False

def create_verification_script():
    """Create a script to verify all imports work."""
    verification_script = '''#!/usr/bin/env python3
"""
Import Verification Script

Tests that all modules can be imported successfully.
"""

import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🔍 Verifying imports...")

failed_imports = []
services_to_test = [
    'app.services.conversational_mission_planner',
    'app.services.coordination_engine',
    'app.services.emergency_service',
    'app.services.analytics_engine',
    'app.services.weather_service',
    'app.services.mission_planner',
    'app.services.drone_manager',
    'app.api.missions',
    'app.api.drones',
    'app.api.chat',
    'app.api.websocket',
    'app.models.mission',
    'app.models.drone',
    'app.models.discovery',
    'app.ai.ollama_client',
    'app.core.config',
    'app.core.database',
    'app.utils.logging'
]

for service in services_to_test:
    try:
        __import__(service)
        print(f"✅ {service}")
    except Exception as e:
        print(f"❌ {service}: {e}")
        failed_imports.append(service)

if failed_imports:
    print(f"\\n❌ FAILED: {len(failed_imports)}/{len(services_to_test)} imports")
    sys.exit(1)
else:
    print(f"\\n✅ SUCCESS: All {len(services_to_test)} services imported successfully")
'''

    with open('backend/verify_imports.py', 'w') as f:
        f.write(verification_script)

    print("✅ Created verification script: backend/verify_imports.py")

def main():
    """Main function to fix all imports."""
    print("🚀 Starting Universal Import Fixer for SAR Drone System")
    print("=" * 60)

    # Find all Python files
    python_files = find_python_files('backend/app')
    print(f"📋 Found {len(python_files)} Python files to process")

    # Process each file
    fixed_count = 0
    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1

    # Create verification script
    create_verification_script()

    print("\n" + "=" * 60)
    print("📊 Import Fix Summary:")
    print(f"  Files processed: {len(python_files)}")
    print(f"  Files fixed: {fixed_count}")
    print(f"  Success rate: {fixed_count/len(python_files)*100:.1f}%" if python_files else "N/A")

    if fixed_count > 0:
        print("\n✅ Import fixes applied successfully!")
        print("🔍 Run 'python3 backend/verify_imports.py' to test all imports")
    else:
        print("\n⚠️ No import issues found or all files already properly configured")

if __name__ == "__main__":
    main()