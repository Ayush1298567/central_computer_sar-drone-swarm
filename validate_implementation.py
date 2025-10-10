#!/usr/bin/env python3
"""
Backend Implementation Validator
Validates that all backend components are properly implemented without placeholders.
"""

import os
import re
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple, Set

class BackendValidator:
    def __init__(self, backend_path: str = "backend"):
        self.backend_path = Path(backend_path)
        self.errors = []
        self.warnings = []
        self.passed_checks = 0
        self.total_checks = 0
        
        # Critical files that must exist and be implemented
        self.critical_files = {
            "services/websocket_manager.py": "WebSocket connection handling",
            "agents/mission_planning/question_generator.py": "AI question generation",
            "app/services/video_stream_receiver.py": "Video processing",
            "app/communication/protocols/mavlink_connection.py": "MAVLink protocol",
            "app/websocket/real_time_bridge.py": "Redis → WebSocket bridge",
            "app/algorithms/area_division.py": "Area division algorithms",
            "app/algorithms/waypoint_generation.py": "Waypoint generation",
            "app/ai/conversation.py": "Conversational AI",
            "app/ai/ollama_client.py": "Ollama AI client",
            "app/services/mission_planner.py": "Mission planning service",
            "app/services/drone_manager.py": "Drone management",
            "app/services/real_mission_execution.py": "Mission execution",
            "app/communication/drone_connection_hub.py": "Drone connection hub",
            "app/core/database.py": "Database management",
            "app/core/config.py": "Configuration management",
            "app/main.py": "FastAPI application",
            "app/api/api_v1/api.py": "API router",
            "app/models/mission.py": "Mission models",
            "app/models/drone.py": "Drone models",
            "app/models/chat.py": "Chat models"
        }
        
        # Forbidden patterns that indicate placeholder code
        self.forbidden_patterns = [
            (r'^\s*pass\s*$', "standalone pass statement"),  # Only catch standalone pass
            (r'\bTODO\b', "TODO comment"),
            (r'\bNotImplementedError\b', "NotImplementedError"),
            (r'return\s*{\s*"status":\s*"success"\s*}', "hardcoded success return"),
            (r'return\s*{\s*"message":\s*"success"\s*}', "hardcoded success message"),
            (r'#\s*TODO:', "TODO comment"),
            (r'#\s*FIXME:', "FIXME comment"),
            (r'#\s*HACK:', "HACK comment"),
            (r'raise\s+NotImplementedError', "NotImplementedError raise"),
            (r'\.lower\(\)\s*in\s*\[', "keyword matching pattern"),
            (r'if\s+.*\s+in\s+.*\.lower\(\)', "keyword matching if statement"),
        ]
        
        # Required imports for real implementations
        self.required_imports = {
            "shapely": "Shapely for geometric operations",
            "ollama": "Ollama for AI features",
            "websockets": "WebSocket support",
            "redis": "Redis for caching",
            "sqlalchemy": "Database ORM",
            "fastapi": "Web framework",
            "pydantic": "Data validation",
            "asyncio": "Async programming",
            "logging": "Logging framework",
            "json": "JSON handling",
            "datetime": "Date/time handling",
            "typing": "Type hints",
            "uuid": "UUID generation",
            "httpx": "HTTP client",
            "aioredis": "Async Redis client"
        }

    def validate_file_exists(self, file_path: str) -> bool:
        """Check if a critical file exists"""
        full_path = self.backend_path / file_path
        exists = full_path.exists()
        if not exists:
            self.errors.append(f"❌ Missing critical file: {file_path}")
        else:
            self.passed_checks += 1
        self.total_checks += 1
        return exists

    def validate_no_placeholders(self, file_path: str) -> bool:
        """Check if file contains placeholder code"""
        full_path = self.backend_path / file_path
        if not full_path.exists():
            return False
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            found_placeholders = []
            for pattern, description in self.forbidden_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Filter out legitimate pass statements
                    if "pass" in description:
                        filtered_matches = []
                        for match in matches:
                            # Check if this pass is legitimate
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if re.search(r'^\s*' + re.escape(match.strip()) + r'\s*$', line):
                                    # Check if this is in a class definition or exception handling
                                    context_start = max(0, i - 10)
                                    context = '\n'.join(lines[context_start:i+1])
                                    
                                    # Allow pass in class definitions
                                    if re.search(r'class\s+\w+.*:', context):
                                        continue  # Skip this match
                                    
                                    # Allow pass in exception handling
                                    if re.search(r'except\s+.*:', context) or re.search(r'finally\s*:', context):
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

    def validate_imports(self, file_path: str) -> bool:
        """Check if file has proper imports for real implementation"""
        full_path = self.backend_path / file_path
        if not full_path.exists():
            return False
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required imports based on file type
            required_for_file = []
            if "ai" in file_path:
                required_for_file.extend(["ollama", "json", "asyncio"])
            if "websocket" in file_path:
                required_for_file.extend(["websockets", "asyncio", "json"])
            if "algorithm" in file_path:
                required_for_file.extend(["shapely", "numpy"])
            if "database" in file_path:
                required_for_file.extend(["sqlalchemy", "asyncio"])
            if "api" in file_path:
                required_for_file.extend(["fastapi", "pydantic", "httpx"])
            
            missing_imports = []
            for imp in required_for_file:
                if imp not in content:
                    missing_imports.append(imp)
            
            if missing_imports:
                self.warnings.append(f"⚠️  {file_path} missing imports: {', '.join(missing_imports)}")
                return False
            else:
                self.passed_checks += 1
                return True
                
        except Exception as e:
            self.errors.append(f"❌ Error checking imports in {file_path}: {e}")
            return False
        
        self.total_checks += 1

    def validate_syntax(self, file_path: str) -> bool:
        """Check if Python file has valid syntax"""
        full_path = self.backend_path / file_path
        if not full_path.exists() or not file_path.endswith('.py'):
            return True
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the file
            ast.parse(content)
            self.passed_checks += 1
            return True
            
        except SyntaxError as e:
            self.errors.append(f"❌ Syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"❌ Error parsing {file_path}: {e}")
            return False
        
        self.total_checks += 1

    def validate_algorithm_implementations(self) -> bool:
        """Validate that algorithms use proper libraries"""
        algorithm_files = [
            "app/algorithms/area_division.py",
            "app/algorithms/waypoint_generation.py"
        ]
        
        all_valid = True
        for file_path in algorithm_files:
            full_path = self.backend_path / file_path
            if not full_path.exists():
                self.errors.append(f"❌ Missing algorithm file: {file_path}")
                all_valid = False
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for Shapely usage
                if "shapely" not in content.lower():
                    self.errors.append(f"❌ {file_path} not using Shapely for geometric operations")
                    all_valid = False
                elif "from shapely.geometry import" in content:
                    self.passed_checks += 1
                
                # Check for real geometric operations
                if ".intersection(" not in content and ".union(" not in content:
                    self.warnings.append(f"⚠️  {file_path} may not be using real geometric operations")
                
            except Exception as e:
                self.errors.append(f"❌ Error checking {file_path}: {e}")
                all_valid = False
            
            self.total_checks += 1
        
        return all_valid

    def validate_ai_implementations(self) -> bool:
        """Validate that AI components use real Ollama calls"""
        ai_files = [
            "app/ai/conversation.py",
            "app/ai/ollama_client.py"
        ]
        
        all_valid = True
        for file_path in ai_files:
            full_path = self.backend_path / file_path
            if not full_path.exists():
                self.errors.append(f"❌ Missing AI file: {file_path}")
                all_valid = False
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for real Ollama usage
                if "ollama" not in content.lower():
                    self.errors.append(f"❌ {file_path} not using Ollama for AI features")
                    all_valid = False
                elif "ollama_client" in content or "ollama.generate" in content:
                    self.passed_checks += 1
                
                # Check for keyword matching (forbidden)
                if "in message.lower()" in content or "if" in content and "in" in content and ".lower()" in content:
                    self.errors.append(f"❌ {file_path} using keyword matching instead of AI")
                    all_valid = False
                
            except Exception as e:
                self.errors.append(f"❌ Error checking {file_path}: {e}")
                all_valid = False
            
            self.total_checks += 1
        
        return all_valid

    def validate_websocket_implementations(self) -> bool:
        """Validate WebSocket implementations"""
        websocket_files = [
            "app/api/websocket.py",
            "services/websocket_manager.py"
        ]
        
        all_valid = True
        for file_path in websocket_files:
            full_path = self.backend_path / file_path
            if not full_path.exists():
                self.errors.append(f"❌ Missing WebSocket file: {file_path}")
                all_valid = False
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for real WebSocket usage
                if "websocket" not in content.lower():
                    self.errors.append(f"❌ {file_path} not implementing WebSocket functionality")
                    all_valid = False
                elif "WebSocket" in content or "websockets" in content:
                    self.passed_checks += 1
                
            except Exception as e:
                self.errors.append(f"❌ Error checking {file_path}: {e}")
                all_valid = False
            
            self.total_checks += 1
        
        return all_valid

    def run_validation(self) -> bool:
        """Run all validation checks"""
        print("🔍 Starting Backend Implementation Validation...")
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
        
        # Check syntax
        print("\n🐍 Checking Python syntax...")
        for file_path in self.critical_files.keys():
            if self.validate_file_exists(file_path):
                if self.validate_syntax(file_path):
                    print(f"✅ {file_path} - Valid syntax")
                else:
                    print(f"❌ {file_path} - Syntax errors")
        
        # Check imports
        print("\n📦 Checking imports...")
        for file_path in self.critical_files.keys():
            if self.validate_file_exists(file_path):
                if self.validate_imports(file_path):
                    print(f"✅ {file_path} - Proper imports")
                else:
                    print(f"⚠️  {file_path} - Missing imports")
        
        # Check algorithm implementations
        print("\n🧮 Checking algorithm implementations...")
        if self.validate_algorithm_implementations():
            print("✅ Algorithms using proper libraries")
        else:
            print("❌ Algorithm implementations need work")
        
        # Check AI implementations
        print("\n🤖 Checking AI implementations...")
        if self.validate_ai_implementations():
            print("✅ AI using real Ollama calls")
        else:
            print("❌ AI implementations need work")
        
        # Check WebSocket implementations
        print("\n🌐 Checking WebSocket implementations...")
        if self.validate_websocket_implementations():
            print("✅ WebSocket implementations found")
        else:
            print("❌ WebSocket implementations need work")
        
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
        
        if len(self.errors) == 0 and success_rate >= 90:
            print("\n🎉 ALL CHECKS PASSED - SYSTEM IS READY")
            return True
        else:
            print(f"\n❌ VALIDATION FAILED - {len(self.errors)} errors found")
            return False

def main():
    """Main validation function"""
    validator = BackendValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()