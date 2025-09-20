#!/usr/bin/env python3
"""
API Structure Validation Script
Tests the API endpoints structure and basic functionality without external dependencies
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_file_structure():
    """Validate that all required files exist"""
    logger.info("🔍 Validating file structure...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/models/__init__.py",
        "app/models/mission.py",
        "app/models/drone.py",
        "app/models/chat.py",
        "app/services/__init__.py",
        "app/services/mission_planner.py",
        "app/services/drone_manager.py",
        "app/services/notification_service.py",
        "app/services/conversational_mission_planner.py",
        "app/api/__init__.py",
        "app/api/missions.py",
        "app/api/drones.py",
        "app/api/chat.py",
        "app/api/websocket.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            logger.info(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            logger.error(f"❌ {file_path}")
    
    logger.info(f"\n📊 File Structure Summary:")
    logger.info(f"Total files: {len(required_files)}")
    logger.info(f"Existing: {len(existing_files)}")
    logger.info(f"Missing: {len(missing_files)}")
    
    return len(missing_files) == 0

def validate_python_syntax():
    """Validate Python syntax for all Python files"""
    logger.info("\n🐍 Validating Python syntax...")
    
    python_files = []
    for root, dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    syntax_errors = []
    valid_files = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Compile to check syntax
            compile(content, file_path, 'exec')
            valid_files.append(file_path)
            logger.info(f"✅ {file_path}")
            
        except SyntaxError as e:
            syntax_errors.append((file_path, str(e)))
            logger.error(f"❌ {file_path}: {e}")
        except Exception as e:
            syntax_errors.append((file_path, str(e)))
            logger.error(f"❌ {file_path}: {e}")
    
    logger.info(f"\n📊 Syntax Validation Summary:")
    logger.info(f"Total Python files: {len(python_files)}")
    logger.info(f"Valid syntax: {len(valid_files)}")
    logger.info(f"Syntax errors: {len(syntax_errors)}")
    
    return len(syntax_errors) == 0

def validate_api_endpoints():
    """Validate API endpoint definitions"""
    logger.info("\n🌐 Validating API endpoint definitions...")
    
    endpoint_files = [
        ("app/api/missions.py", "Mission API"),
        ("app/api/drones.py", "Drone API"),
        ("app/api/chat.py", "Chat API"),
        ("app/api/websocket.py", "WebSocket API")
    ]
    
    endpoint_stats = {}
    
    for file_path, api_name in endpoint_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count endpoints
            post_endpoints = content.count("@router.post(")
            get_endpoints = content.count("@router.get(")
            patch_endpoints = content.count("@router.patch(")
            delete_endpoints = content.count("@router.delete(")
            websocket_endpoints = content.count("@router.websocket(")
            
            total_endpoints = post_endpoints + get_endpoints + patch_endpoints + delete_endpoints + websocket_endpoints
            
            endpoint_stats[api_name] = {
                "POST": post_endpoints,
                "GET": get_endpoints,
                "PATCH": patch_endpoints,
                "DELETE": delete_endpoints,
                "WebSocket": websocket_endpoints,
                "Total": total_endpoints
            }
            
            logger.info(f"✅ {api_name}: {total_endpoints} endpoints")
            logger.info(f"   POST: {post_endpoints}, GET: {get_endpoints}, PATCH: {patch_endpoints}, DELETE: {delete_endpoints}, WS: {websocket_endpoints}")
            
        except Exception as e:
            logger.error(f"❌ Error validating {api_name}: {e}")
            endpoint_stats[api_name] = {"Error": str(e)}
    
    return endpoint_stats

def validate_models():
    """Validate data models"""
    logger.info("\n📋 Validating data models...")
    
    model_files = [
        ("app/models/mission.py", "Mission Models"),
        ("app/models/drone.py", "Drone Models"),
        ("app/models/chat.py", "Chat Models")
    ]
    
    model_stats = {}
    
    for file_path, model_name in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count model definitions
            pydantic_models = content.count("class ") - content.count("class Config:")
            enums = content.count("class ") if "Enum)" in content else 0
            sqlalchemy_models = content.count("__tablename__")
            
            model_stats[model_name] = {
                "Classes": pydantic_models,
                "SQLAlchemy Tables": sqlalchemy_models,
                "Has Enums": "Enum)" in content
            }
            
            logger.info(f"✅ {model_name}: {pydantic_models} classes, {sqlalchemy_models} tables")
            
        except Exception as e:
            logger.error(f"❌ Error validating {model_name}: {e}")
            model_stats[model_name] = {"Error": str(e)}
    
    return model_stats

def validate_services():
    """Validate service implementations"""
    logger.info("\n⚙️ Validating service implementations...")
    
    service_files = [
        ("app/services/mission_planner.py", "Mission Planner"),
        ("app/services/drone_manager.py", "Drone Manager"),
        ("app/services/notification_service.py", "Notification Service"),
        ("app/services/conversational_mission_planner.py", "Conversational Planner")
    ]
    
    service_stats = {}
    
    for file_path, service_name in service_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count methods
            async_methods = content.count("async def ")
            sync_methods = content.count("def ") - async_methods
            classes = content.count("class ")
            
            service_stats[service_name] = {
                "Classes": classes,
                "Async Methods": async_methods,
                "Sync Methods": sync_methods,
                "Total Methods": async_methods + sync_methods
            }
            
            logger.info(f"✅ {service_name}: {classes} classes, {async_methods + sync_methods} methods")
            
        except Exception as e:
            logger.error(f"❌ Error validating {service_name}: {e}")
            service_stats[service_name] = {"Error": str(e)}
    
    return service_stats

def generate_validation_report():
    """Generate comprehensive validation report"""
    logger.info("\n📊 Generating comprehensive validation report...")
    
    report = {
        "validation_timestamp": datetime.utcnow().isoformat(),
        "python_version": sys.version,
        "working_directory": os.getcwd()
    }
    
    # Run all validations
    report["file_structure_valid"] = validate_file_structure()
    report["syntax_valid"] = validate_python_syntax()
    report["endpoint_stats"] = validate_api_endpoints()
    report["model_stats"] = validate_models()
    report["service_stats"] = validate_services()
    
    # Calculate overall score
    validations = [
        report["file_structure_valid"],
        report["syntax_valid"]
    ]
    
    overall_score = (sum(validations) / len(validations)) * 100
    report["overall_score"] = overall_score
    
    # Summary
    logger.info("\n🎯 VALIDATION SUMMARY:")
    logger.info(f"File Structure: {'✅ PASS' if report['file_structure_valid'] else '❌ FAIL'}")
    logger.info(f"Python Syntax: {'✅ PASS' if report['syntax_valid'] else '❌ FAIL'}")
    logger.info(f"Overall Score: {overall_score:.1f}%")
    
    # Endpoint summary
    total_endpoints = 0
    for api_stats in report["endpoint_stats"].values():
        if isinstance(api_stats, dict) and "Total" in api_stats:
            total_endpoints += api_stats["Total"]
    
    logger.info(f"Total API Endpoints: {total_endpoints}")
    
    # Save report
    report_file = "validation_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"📄 Detailed report saved to: {report_file}")
    
    return report

def main():
    """Main validation function"""
    logger.info("🚀 Starting SAR Drone API Structure Validation")
    logger.info("=" * 60)
    
    try:
        report = generate_validation_report()
        
        if report["overall_score"] == 100.0:
            logger.info("\n🎉 ALL VALIDATIONS PASSED!")
            logger.info("The SAR Drone API structure is complete and ready for testing.")
            return 0
        else:
            logger.warning(f"\n⚠️ VALIDATION INCOMPLETE ({report['overall_score']:.1f}%)")
            logger.warning("Some issues were found. Check the detailed report.")
            return 1
            
    except Exception as e:
        logger.error(f"\n💥 VALIDATION FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())