#!/usr/bin/env python3
"""
Dependency Verification Script
Verifies that all required dependencies are installed and available.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Tuple, Set

class DependencyVerifier:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed_checks = 0
        self.total_checks = 0
        
        # Backend Python dependencies
        self.backend_dependencies = [
            ("fastapi", "FastAPI web framework"),
            ("uvicorn", "ASGI server"),
            ("sqlalchemy", "Database ORM"),
            ("alembic", "Database migrations"),
            ("pydantic", "Data validation"),
            ("httpx", "HTTP client"),
            ("websockets", "WebSocket support"),
            ("aioredis", "Async Redis client"),
            ("shapely", "Geometric operations"),
            ("numpy", "Numerical computing"),
            ("pandas", "Data manipulation"),
            ("scikit-learn", "Machine learning"),
            ("torch", "PyTorch deep learning"),
            ("opencv-python", "Computer vision"),
            ("pillow", "Image processing"),
            ("pymavlink", "MAVLink protocol"),
            ("pyserial", "Serial communication"),
            ("ollama", "Ollama AI client"),
            ("langchain", "LangChain framework"),
            ("qdrant-client", "Vector database"),
            ("chromadb", "Vector database"),
            ("sentence-transformers", "Sentence embeddings"),
            ("faiss-cpu", "Vector similarity search"),
            ("neo4j", "Graph database"),
            ("kafka-python", "Kafka client"),
            ("elasticsearch", "Search engine"),
            ("prometheus-client", "Metrics collection"),
            ("structlog", "Structured logging"),
            ("python-jose", "JWT handling"),
            ("passlib", "Password hashing"),
            ("geopandas", "Geospatial data"),
            ("folium", "Interactive maps"),
            ("plotly", "Interactive visualizations"),
            ("osmnx", "OpenStreetMap data"),
            ("faker", "Data generation"),
            ("scipy", "Scientific computing"),
            ("psutil", "System monitoring"),
            ("pytest", "Testing framework"),
            ("pytest-asyncio", "Async testing"),
        ]
        
        # Frontend dependencies (from package.json)
        self.frontend_dependencies = [
            ("react", "React library"),
            ("react-dom", "React DOM"),
            ("typescript", "TypeScript compiler"),
            ("vite", "Build tool"),
            ("axios", "HTTP client"),
            ("leaflet", "Map library"),
            ("react-leaflet", "React map components"),
            ("@types/react", "React TypeScript types"),
            ("@types/react-dom", "React DOM TypeScript types"),
            ("tailwindcss", "CSS framework"),
            ("@tailwindcss/forms", "Tailwind forms plugin"),
            ("@tailwindcss/typography", "Tailwind typography plugin"),
            ("autoprefixer", "CSS autoprefixer"),
            ("postcss", "CSS processor"),
            ("vitest", "Testing framework"),
            ("@testing-library/react", "React testing utilities"),
            ("@testing-library/jest-dom", "Jest DOM matchers"),
        ]

    def check_python_package(self, package_name: str, description: str) -> bool:
        """Check if a Python package is installed and importable"""
        try:
            # Try to import the package
            importlib.import_module(package_name)
            self.passed_checks += 1
            return True
        except ImportError:
            self.errors.append(f"❌ Missing Python package: {package_name} - {description}")
            return False
        except Exception as e:
            self.warnings.append(f"⚠️  Error importing {package_name}: {e}")
            return False
        finally:
            self.total_checks += 1

    def check_node_package(self, package_name: str, description: str) -> bool:
        """Check if a Node.js package is installed"""
        try:
            # Check if package exists in node_modules
            frontend_path = Path("frontend")
            if not frontend_path.exists():
                self.errors.append(f"❌ Frontend directory not found")
                return False
            
            package_json_path = frontend_path / "package.json"
            if not package_json_path.exists():
                self.errors.append(f"❌ package.json not found in frontend directory")
                return False
            
            # Read package.json to check dependencies
            import json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            if package_name in all_deps:
                self.passed_checks += 1
                return True
            else:
                self.errors.append(f"❌ Missing Node.js package: {package_name} - {description}")
                return False
                
        except Exception as e:
            self.errors.append(f"❌ Error checking Node.js package {package_name}: {e}")
            return False
        finally:
            self.total_checks += 1

    def check_system_requirements(self) -> bool:
        """Check system requirements"""
        print("\n🖥️  Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            self.passed_checks += 1
        else:
            self.errors.append(f"❌ Python version {python_version.major}.{python_version.minor} is too old. Need Python 3.8+")
        self.total_checks += 1
        
        # Check Node.js version
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"✅ Node.js {node_version}")
                self.passed_checks += 1
            else:
                self.errors.append("❌ Node.js not found or not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.errors.append("❌ Node.js not found")
        self.total_checks += 1
        
        # Check npm version
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                npm_version = result.stdout.strip()
                print(f"✅ npm {npm_version}")
                self.passed_checks += 1
            else:
                self.errors.append("❌ npm not found or not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.errors.append("❌ npm not found")
        self.total_checks += 1
        
        return len(self.errors) == 0

    def check_backend_dependencies(self) -> bool:
        """Check all backend Python dependencies"""
        print("\n🐍 Checking backend Python dependencies...")
        
        all_valid = True
        for package_name, description in self.backend_dependencies:
            if self.check_python_package(package_name, description):
                print(f"✅ {package_name} - {description}")
            else:
                print(f"❌ {package_name} - {description}")
                all_valid = False
        
        return all_valid

    def check_frontend_dependencies(self) -> bool:
        """Check all frontend Node.js dependencies"""
        print("\n📦 Checking frontend Node.js dependencies...")
        
        all_valid = True
        for package_name, description in self.frontend_dependencies:
            if self.check_node_package(package_name, description):
                print(f"✅ {package_name} - {description}")
            else:
                print(f"❌ {package_name} - {description}")
                all_valid = False
        
        return all_valid

    def check_optional_services(self) -> bool:
        """Check optional external services"""
        print("\n🔧 Checking optional services...")
        
        # Check Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            print("✅ Redis - Connected")
            self.passed_checks += 1
        except Exception:
            self.warnings.append("⚠️  Redis not available (optional for development)")
        self.total_checks += 1
        
        # Check PostgreSQL
        try:
            import psycopg2
            print("✅ PostgreSQL driver - Available")
            self.passed_checks += 1
        except ImportError:
            self.warnings.append("⚠️  PostgreSQL driver not available (optional for development)")
        self.total_checks += 1
        
        # Check Ollama
        try:
            import ollama
            print("✅ Ollama client - Available")
            self.passed_checks += 1
        except ImportError:
            self.warnings.append("⚠️  Ollama client not available (required for AI features)")
        self.total_checks += 1
        
        return True

    def run_verification(self) -> bool:
        """Run all dependency verification checks"""
        print("🔍 Starting Dependency Verification...")
        print("=" * 60)
        
        # Check system requirements
        system_ok = self.check_system_requirements()
        
        # Check backend dependencies
        backend_ok = self.check_backend_dependencies()
        
        # Check frontend dependencies
        frontend_ok = self.check_frontend_dependencies()
        
        # Check optional services
        services_ok = self.check_optional_services()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DEPENDENCY VERIFICATION SUMMARY")
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
        
        if len(self.errors) == 0:
            print("\n🎉 ALL DEPENDENCIES VERIFIED")
            return True
        else:
            print(f"\n❌ DEPENDENCY VERIFICATION FAILED - {len(self.errors)} errors found")
            return False

def main():
    """Main verification function"""
    verifier = DependencyVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()