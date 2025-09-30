#!/usr/bin/env python3
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
    print(f"\n❌ FAILED: {len(failed_imports)}/{len(services_to_test)} imports")
    sys.exit(1)
else:
    print(f"\n✅ SUCCESS: All {len(services_to_test)} services imported successfully")
