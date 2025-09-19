#!/usr/bin/env python3
"""
SAR Drone System Verification Script
Checks if all components are properly installed and configured.
"""

import sys
import subprocess
import importlib
import requests
import json
import asyncio
import sqlite3
from pathlib import Path

def check_command(command, name):
    """Check if a command is available."""
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True)
        print(f"✅ {name} is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ {name} is not installed")
        return False

def check_python_package(package, name=None):
    """Check if a Python package is installed."""
    if name is None:
        name = package
    try:
        importlib.import_module(package)
        print(f"✅ {name} package is installed")
        return True
    except ImportError:
        print(f"❌ {name} package is not installed")
        return False

def check_node_package(package_json_path):
    """Check if Node.js packages are installed."""
    try:
        if not Path(package_json_path).exists():
            print(f"❌ {package_json_path} not found")
            return False
        
        node_modules_path = Path(package_json_path).parent / "node_modules"
        if node_modules_path.exists():
            print("✅ Node.js packages are installed")
            return True
        else:
            print("❌ Node.js packages are not installed (run npm install)")
            return False
    except Exception as e:
        print(f"❌ Error checking Node.js packages: {e}")
        return False

def check_database():
    """Check if database can be created/accessed."""
    try:
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE test (id INTEGER)')
        conn.close()
        print("✅ Database functionality works")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_ollama():
    """Check if Ollama is running and has required models."""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            required_models = ['llama2', 'codellama']
            missing_models = [model for model in required_models if not any(model in name for name in model_names)]
            
            if missing_models:
                print(f"⚠️  Ollama is running but missing models: {missing_models}")
                print("   Run: ollama pull llama2 && ollama pull codellama")
                return False
            else:
                print("✅ Ollama is running with required models")
                return True
        else:
            print("❌ Ollama is not responding")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running (run: ollama serve)")
        return False

def check_backend_api():
    """Check if backend API is accessible."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend API is running")
            return True
        else:
            print(f"❌ Backend API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend API is not running")
        return False

def check_frontend():
    """Check if frontend is accessible."""
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Frontend is not running")
        return False

def main():
    print("🚁 SAR Drone System Verification")
    print("=================================")
    print()
    
    all_checks_passed = True
    
    # Check system requirements
    print("📋 System Requirements")
    print("---------------------")
    all_checks_passed &= check_command('python3', 'Python 3')
    all_checks_passed &= check_command('node', 'Node.js')
    all_checks_passed &= check_command('npm', 'npm')
    all_checks_passed &= check_command('ollama', 'Ollama')
    print()
    
    # Check Python packages
    print("🐍 Python Dependencies")
    print("----------------------")
    python_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pydantic', 'Pydantic'),
        ('asyncio', 'AsyncIO'),
        ('aiofiles', 'AIOFiles')
    ]
    
    for package, name in python_packages:
        all_checks_passed &= check_python_package(package, name)
    
    all_checks_passed &= check_database()
    print()
    
    # Check Node.js packages
    print("📦 Node.js Dependencies")
    print("-----------------------")
    all_checks_passed &= check_node_package('frontend/package.json')
    print()
    
    # Check services
    print("🔧 Services")
    print("-----------")
    ollama_ok = check_ollama()
    backend_ok = check_backend_api()
    frontend_ok = check_frontend()
    
    all_checks_passed &= ollama_ok
    # Don't fail overall check if services aren't running - they might not be started yet
    print()
    
    # Check file structure
    print("📁 File Structure")
    print("-----------------")
    required_files = [
        'backend/app/main.py',
        'backend/requirements.txt',
        'frontend/package.json',
        'frontend/src/App.tsx',
        'setup.sh',
        'README.md'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} is missing")
            all_checks_passed = False
    
    print()
    print("📊 Verification Summary")
    print("======================")
    
    if all_checks_passed:
        print("✅ All critical components are properly installed!")
        print()
        if not (backend_ok and frontend_ok):
            print("ℹ️  To start the system:")
            print("   1. Terminal 1: ollama serve")
            print("   2. Terminal 2: cd backend && uvicorn app.main:app --reload")
            print("   3. Terminal 3: cd frontend && npm start")
            print("   4. Open http://localhost:3000")
    else:
        print("❌ Some components are missing or not configured properly.")
        print("   Run ./setup.sh to install missing components.")
        sys.exit(1)

if __name__ == "__main__":
    main()