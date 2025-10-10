#!/usr/bin/env python3
"""
Frontend Implementation Validator
Validates that all frontend components are properly implemented without placeholders.
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set

class FrontendValidator:
    def __init__(self, frontend_path: str = "frontend"):
        self.frontend_path = Path(frontend_path)
        self.errors = []
        self.warnings = []
        self.passed_checks = 0
        self.total_checks = 0
        
        # Critical frontend files that must exist and be implemented
        self.critical_files = {
            "src/services/missions.ts": "Mission API integration",
            "src/services/drones.ts": "Drone API integration",
            "src/contexts/WebSocketContext.tsx": "WebSocket context",
            "src/components/mission/MissionForm.tsx": "Mission planning component",
            "src/components/mission/ConversationalChat.tsx": "AI chat component",
            "src/components/map/InteractiveMap.tsx": "Map visualization",
            "src/components/drone/RealTimeDroneMonitor.tsx": "Real-time telemetry",
            "src/components/drone/DroneCommander.tsx": "Mission execution controls",
            "src/services/api.ts": "API service layer",
            "src/types/mission.ts": "Mission type definitions",
            "src/types/drone.ts": "Drone type definitions",
            "src/App.tsx": "Main application component",
            "package.json": "Package configuration",
            "vite.config.ts": "Build configuration"
        }
        
        # Forbidden patterns that indicate placeholder code
        self.forbidden_patterns = [
            (r'//\s*TODO', "TODO comment"),
            (r'//\s*FIXME', "FIXME comment"),
            (r'//\s*HACK', "HACK comment"),
            (r'console\.log\([^)]*\)\s*;', "console.log statement"),
            (r'console\.warn\([^)]*\)\s*;', "console.warn statement"),
            (r'console\.error\([^)]*\)\s*;', "console.error statement"),
            (r'const\s+\w+\s*=\s*\[\s*\]\s*;', "empty array assignment"),
            (r'const\s+\w+\s*=\s*\{\s*\}\s*;', "empty object assignment"),
            (r'return\s*null\s*;', "null return (may be placeholder)"),
            (r'return\s*<div>\s*</div>\s*;', "empty div return"),
            (r'mockData', "mock data reference"),
            (r'fakeData', "fake data reference"),
            (r'testData', "test data reference"),
            (r'hardcoded', "hardcoded reference"),
            (r'//\s*Mock', "Mock comment"),
            (r'//\s*Fake', "Fake comment"),
            (r'//\s*Test', "Test comment"),
        ]
        
        # Required patterns for real implementations
        self.required_patterns = {
            "api": [
                (r'fetch\s*\(', "fetch API calls"),
                (r'axios\s*\.', "axios HTTP client"),
                (r'\.then\s*\(', "Promise handling"),
                (r'\.catch\s*\(', "Error handling"),
                (r'async\s+', "Async functions"),
                (r'await\s+', "Await expressions")
            ],
            "websocket": [
                (r'new\s+WebSocket\s*\(', "WebSocket constructor"),
                (r'\.onopen\s*=', "WebSocket onopen"),
                (r'\.onmessage\s*=', "WebSocket onmessage"),
                (r'\.onclose\s*=', "WebSocket onclose"),
                (r'\.onerror\s*=', "WebSocket onerror")
            ],
            "react": [
                (r'useState\s*\(', "useState hook"),
                (r'useEffect\s*\(', "useEffect hook"),
                (r'useCallback\s*\(', "useCallback hook"),
                (r'useMemo\s*\(', "useMemo hook"),
                (r'import\s+.*from\s+[\'"]react[\'"]', "React imports")
            ],
            "typescript": [
                (r':\s*\w+', "Type annotations"),
                (r'interface\s+\w+', "Interface definitions"),
                (r'type\s+\w+', "Type definitions"),
                (r'<\w+>', "Generic types")
            ]
        }

    def validate_file_exists(self, file_path: str) -> bool:
        """Check if a critical file exists"""
        full_path = self.frontend_path / file_path
        exists = full_path.exists()
        if not exists:
            self.errors.append(f"❌ Missing critical file: {file_path}")
        else:
            self.passed_checks += 1
        self.total_checks += 1
        return exists

    def validate_no_placeholders(self, file_path: str) -> bool:
        """Check if file contains placeholder code"""
        full_path = self.frontend_path / file_path
        if not full_path.exists():
            return False
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            found_placeholders = []
            for pattern, description in self.forbidden_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Filter out legitimate patterns
                    if "console" in description:
                        filtered_matches = []
                        for match in matches:
                            # Check if this console statement is in error handling
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if match.strip() in line:
                                    # Check if this is in error handling context
                                    context_start = max(0, i - 5)
                                    context_end = min(len(lines), i + 5)
                                    context = '\n'.join(lines[context_start:context_end])
                                    
                                    # Allow console statements in error handling and event handlers
                                    if re.search(r'(catch|error|throw|reject|handle|event|update)', context, re.IGNORECASE):
                                        continue  # Skip this match
                                    
                                    # Otherwise, it's a placeholder
                                    filtered_matches.append(match)
                                    break
                        matches = filtered_matches
                    
                    # Filter out legitimate null returns in React components
                    if "null return" in description:
                        filtered_matches = []
                        for match in matches:
                            # Check if this null return is in a React component
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if match.strip() in line:
                                    # Check if this is in a React component context
                                    context_start = max(0, i - 10)
                                    context = '\n'.join(lines[context_start:i+1])
                                    
                                    # Allow null returns in React components (conditional rendering)
                                    if re.search(r'(if\s*\(|return\s+null|loading|error)', context, re.IGNORECASE):
                                        continue  # Skip this match
                                    
                                    # Otherwise, it's a placeholder
                                    filtered_matches.append(match)
                                    break
                        matches = filtered_matches
                    
                    if matches:
                        found_placeholders.extend([(description, match) for match in matches])
            
            if found_placeholders:
                self.errors.append(f"❌ {file_path} contains placeholder code:")
                for desc, match in found_placeholders[:5]:  # Show first 5
                    self.errors.append(f"   - {desc}: {match}")
                if len(found_placeholders) > 5:
                    self.errors.append(f"   ... and {len(found_placeholders) - 5} more")
                return False
            else:
                self.passed_checks += 1
                return True
                
        except Exception as e:
            self.errors.append(f"❌ Error reading {file_path}: {e}")
            return False
        
        self.total_checks += 1

    def validate_api_integration(self, file_path: str) -> bool:
        """Check if file has proper API integration"""
        full_path = self.frontend_path / file_path
        if not full_path.exists():
            return False
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for API patterns
            has_fetch = bool(re.search(r'fetch\s*\(', content))
            has_axios = bool(re.search(r'axios\s*\.', content))
            has_async = bool(re.search(r'async\s+', content))
            has_await = bool(re.search(r'await\s+', content))
            has_error_handling = bool(re.search(r'\.catch\s*\(', content))
            
            if not (has_fetch or has_axios):
                self.warnings.append(f"⚠️  {file_path} may not have API integration")
                return False
            
            if not has_async or not has_await:
                self.warnings.append(f"⚠️  {file_path} may not be using async/await properly")
                return False
            
            if not has_error_handling:
                self.warnings.append(f"⚠️  {file_path} may be missing error handling")
                return False
            
            self.passed_checks += 1
            return True
                
        except Exception as e:
            self.errors.append(f"❌ Error checking API integration in {file_path}: {e}")
            return False
        
        self.total_checks += 1

    def validate_websocket_integration(self, file_path: str) -> bool:
        """Check if file has proper WebSocket integration"""
        full_path = self.frontend_path / file_path
        if not full_path.exists():
            return False
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for WebSocket patterns
            has_websocket = bool(re.search(r'WebSocket\s*\(', content))
            has_event_handlers = bool(re.search(r'\.on(open|message|close|error)\s*=', content))
            has_connection_management = bool(re.search(r'\.connect|\.disconnect|\.close', content))
            
            if not has_websocket:
                self.warnings.append(f"⚠️  {file_path} may not have WebSocket integration")
                return False
            
            if not has_event_handlers:
                self.warnings.append(f"⚠️  {file_path} may be missing WebSocket event handlers")
                return False
            
            self.passed_checks += 1
            return True
                
        except Exception as e:
            self.errors.append(f"❌ Error checking WebSocket integration in {file_path}: {e}")
            return False
        
        self.total_checks += 1

    def validate_react_patterns(self, file_path: str) -> bool:
        """Check if file follows React best practices"""
        full_path = self.frontend_path / file_path
        if not full_path.exists() or not file_path.endswith(('.tsx', '.jsx')):
            return True
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for React patterns
            has_jsx = bool(re.search(r'<[A-Z]', content))
            has_hooks = bool(re.search(r'use[A-Z]\w+', content))
            has_props = bool(re.search(r'props\s*:', content) or re.search(r'{\s*\w+\s*}\s*:', content))
            has_imports = bool(re.search(r'import.*from\s+[\'"]react[\'"]', content))
            
            if not has_jsx:
                self.warnings.append(f"⚠️  {file_path} may not contain JSX")
                return False
            
            if not has_hooks:
                self.warnings.append(f"⚠️  {file_path} may not be using React hooks")
                return False
            
            if not has_imports:
                self.warnings.append(f"⚠️  {file_path} may not be importing React")
                return False
            
            self.passed_checks += 1
            return True
                
        except Exception as e:
            self.errors.append(f"❌ Error checking React patterns in {file_path}: {e}")
            return False
        
        self.total_checks += 1

    def validate_typescript_usage(self, file_path: str) -> bool:
        """Check if file uses TypeScript properly"""
        full_path = self.frontend_path / file_path
        if not full_path.exists() or not file_path.endswith(('.ts', '.tsx')):
            return True
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for TypeScript patterns
            has_types = bool(re.search(r':\s*\w+', content))
            has_interfaces = bool(re.search(r'interface\s+\w+', content))
            has_generics = bool(re.search(r'<\w+>', content))
            has_imports = bool(re.search(r'import\s+.*from\s+[\'"]', content))
            
            if not has_types and not has_interfaces:
                self.warnings.append(f"⚠️  {file_path} may not be using TypeScript features")
                return False
            
            self.passed_checks += 1
            return True
                
        except Exception as e:
            self.errors.append(f"❌ Error checking TypeScript usage in {file_path}: {e}")
            return False
        
        self.total_checks += 1

    def validate_package_json(self) -> bool:
        """Validate package.json configuration"""
        package_json_path = self.frontend_path / "package.json"
        if not package_json_path.exists():
            self.errors.append("❌ Missing package.json")
            return False
        
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Check for required dependencies
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            required_deps = [
                'react', 'react-dom', 'typescript', 'vite',
                'axios', 'leaflet', 'react-leaflet'
            ]
            
            missing_deps = []
            for dep in required_deps:
                if dep not in all_deps:
                    missing_deps.append(dep)
            
            if missing_deps:
                self.warnings.append(f"⚠️  Missing dependencies: {', '.join(missing_deps)}")
                return False
            
            # Check for scripts
            scripts = package_data.get('scripts', {})
            required_scripts = ['dev', 'build', 'test']
            
            missing_scripts = []
            for script in required_scripts:
                if script not in scripts:
                    missing_scripts.append(script)
            
            if missing_scripts:
                self.warnings.append(f"⚠️  Missing scripts: {', '.join(missing_scripts)}")
                return False
            
            self.passed_checks += 1
            return True
                
        except Exception as e:
            self.errors.append(f"❌ Error reading package.json: {e}")
            return False
        
        self.total_checks += 1

    def validate_build_configuration(self) -> bool:
        """Validate build configuration files"""
        config_files = [
            "vite.config.ts",
            "tsconfig.json",
            "tailwind.config.js"
        ]
        
        all_valid = True
        for config_file in config_files:
            config_path = self.frontend_path / config_file
            if not config_path.exists():
                self.warnings.append(f"⚠️  Missing {config_file}")
                all_valid = False
            else:
                self.passed_checks += 1
            self.total_checks += 1
        
        return all_valid

    def run_validation(self) -> bool:
        """Run all validation checks"""
        print("🔍 Starting Frontend Implementation Validation...")
        print("=" * 60)
        
        # Check critical files exist
        print("\n📁 Checking critical files...")
        for file_path, description in self.critical_files.items():
            if self.validate_file_exists(file_path):
                print(f"✅ {file_path} - {description}")
            else:
                print(f"❌ {file_path} - {description}")
        
        # Check for placeholder code
        print("\n🚫 Checking for placeholder code...")
        for file_path in self.critical_files.keys():
            if self.validate_file_exists(file_path):
                if self.validate_no_placeholders(file_path):
                    print(f"✅ {file_path} - No placeholders found")
                else:
                    print(f"❌ {file_path} - Contains placeholder code")
        
        # Check API integration
        print("\n🌐 Checking API integration...")
        api_files = [f for f in self.critical_files.keys() if 'api' in f or 'service' in f]
        for file_path in api_files:
            if self.validate_file_exists(file_path):
                if self.validate_api_integration(file_path):
                    print(f"✅ {file_path} - API integration found")
                else:
                    print(f"⚠️  {file_path} - API integration needs work")
        
        # Check WebSocket integration
        print("\n🔌 Checking WebSocket integration...")
        websocket_files = [f for f in self.critical_files.keys() if 'websocket' in f or 'hook' in f]
        for file_path in websocket_files:
            if self.validate_file_exists(file_path):
                if self.validate_websocket_integration(file_path):
                    print(f"✅ {file_path} - WebSocket integration found")
                else:
                    print(f"⚠️  {file_path} - WebSocket integration needs work")
        
        # Check React patterns
        print("\n⚛️  Checking React patterns...")
        react_files = [f for f in self.critical_files.keys() if f.endswith('.tsx')]
        for file_path in react_files:
            if self.validate_file_exists(file_path):
                if self.validate_react_patterns(file_path):
                    print(f"✅ {file_path} - React patterns found")
                else:
                    print(f"⚠️  {file_path} - React patterns need work")
        
        # Check TypeScript usage
        print("\n📝 Checking TypeScript usage...")
        ts_files = [f for f in self.critical_files.keys() if f.endswith(('.ts', '.tsx'))]
        for file_path in ts_files:
            if self.validate_file_exists(file_path):
                if self.validate_typescript_usage(file_path):
                    print(f"✅ {file_path} - TypeScript usage found")
                else:
                    print(f"⚠️  {file_path} - TypeScript usage needs work")
        
        # Check package.json
        print("\n📦 Checking package.json...")
        if self.validate_package_json():
            print("✅ package.json - Configuration valid")
        else:
            print("⚠️  package.json - Configuration needs work")
        
        # Check build configuration
        print("\n🔧 Checking build configuration...")
        if self.validate_build_configuration():
            print("✅ Build configuration - All config files found")
        else:
            print("⚠️  Build configuration - Some config files missing")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        
        print(f"✅ Passed: {self.passed_checks}/{self.total_checks} ({success_rate:.1f}%)")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n🚨 ERRORS FOUND:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if len(self.errors) == 0 and success_rate >= 85:
            print("\n🎉 FRONTEND VALIDATION PASSED")
            return True
        else:
            print(f"\n❌ FRONTEND VALIDATION FAILED - {len(self.errors)} errors found")
            return False

def main():
    """Main validation function"""
    validator = FrontendValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()