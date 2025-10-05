#!/usr/bin/env python3
"""
Start AI-Enhanced SAR System
Starts the complete system with AI decision integration
"""

import asyncio
import logging
import subprocess
import time
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AISystemStarter:
    """Start the AI-enhanced SAR system"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.base_dir = Path(__file__).parent
    
    async def check_local_ai(self) -> bool:
        """Check if local AI (Ollama) is properly set up"""
        try:
            import requests
            
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if required models are available
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            required_models = ["llama3.2:3b", "llama3.2:1b"]
            available_models = [m for m in required_models if m in model_names]
            
            if len(available_models) >= 1:  # At least one model available
                logger.info(f"✅ Local AI ready with models: {available_models}")
                return True
            else:
                logger.warning("⚠️ No required AI models found")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Local AI check failed: {e}")
            return False
        
    async def start_system(self):
        """Start the complete AI system"""
        try:
            logger.info("🚀 Starting AI-Enhanced SAR System")
            
            # Check if we're in the right directory
            if not (self.base_dir / "backend").exists():
                logger.error("❌ Backend directory not found. Please run from project root.")
                return False
            
            # Check if local AI is set up
            logger.info("🤖 Checking local AI setup...")
            if not await self.check_local_ai():
                logger.warning("⚠️ Local AI not properly configured. Run: python setup_local_ai.py")
                logger.info("🔄 Continuing without AI features...")
            
            # Start backend
            logger.info("🔧 Starting backend server...")
            if not await self.start_backend():
                logger.error("❌ Failed to start backend")
                return False
            
            # Wait for backend to be ready
            logger.info("⏳ Waiting for backend to be ready...")
            if not await self.wait_for_backend():
                logger.error("❌ Backend failed to start properly")
                return False
            
            # Start frontend
            logger.info("🎨 Starting frontend server...")
            if not await self.start_frontend():
                logger.error("❌ Failed to start frontend")
                return False
            
            # Wait for frontend to be ready
            logger.info("⏳ Waiting for frontend to be ready...")
            if not await self.wait_for_frontend():
                logger.error("❌ Frontend failed to start properly")
                return False
            
            logger.info("✅ AI-Enhanced SAR System started successfully!")
            logger.info("🌐 Backend: http://localhost:8000")
            logger.info("🎨 Frontend: http://localhost:3000")
            logger.info("🤖 AI Decisions: http://localhost:3000/ai-decisions")
            logger.info("📊 API Docs: http://localhost:8000/docs")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start system: {e}")
            return False
    
    async def start_backend(self) -> bool:
        """Start the backend server"""
        try:
            backend_dir = self.base_dir / "backend"
            
            # Check if virtual environment exists
            venv_python = backend_dir / "venv" / "bin" / "python"
            if not venv_python.exists():
                logger.info("📦 Creating virtual environment...")
                subprocess.run([sys.executable, "-m", "venv", "venv"], cwd=backend_dir, check=True)
                
                logger.info("📦 Installing dependencies...")
                subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                             cwd=backend_dir, check=True)
            
            # Start backend server
            self.backend_process = subprocess.Popen(
                [str(venv_python), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    async def start_frontend(self) -> bool:
        """Start the frontend server"""
        try:
            frontend_dir = self.base_dir / "frontend"
            
            if not frontend_dir.exists():
                logger.error("Frontend directory not found")
                return False
            
            # Check if node_modules exists
            if not (frontend_dir / "node_modules").exists():
                logger.info("📦 Installing frontend dependencies...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            
            # Start frontend server
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            return False
    
    async def wait_for_backend(self, timeout: int = 30) -> bool:
        """Wait for backend to be ready"""
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Backend is ready")
                    return True
            except:
                pass
            
            await asyncio.sleep(1)
        
        return False
    
    async def wait_for_frontend(self, timeout: int = 30) -> bool:
        """Wait for frontend to be ready"""
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:3000", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Frontend is ready")
                    return True
            except:
                pass
            
            await asyncio.sleep(1)
        
        return False
    
    def stop_system(self):
        """Stop the system"""
        logger.info("🛑 Stopping AI-Enhanced SAR System...")
        
        if self.backend_process:
            self.backend_process.terminate()
            logger.info("✅ Backend stopped")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            logger.info("✅ Frontend stopped")
    
    async def run_tests(self):
        """Run AI integration tests"""
        try:
            logger.info("🧪 Running AI integration tests...")
            
            # Import and run the test script
            test_script = self.base_dir / "test_ai_integration.py"
            if test_script.exists():
                result = subprocess.run([sys.executable, str(test_script)], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ All tests passed!")
                    print(result.stdout)
                else:
                    logger.error("❌ Some tests failed!")
                    print(result.stderr)
            else:
                logger.warning("⚠️  Test script not found")
                
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")

async def main():
    """Main function"""
    starter = AISystemStarter()
    
    try:
        # Start the system
        if await starter.start_system():
            logger.info("🎉 System started successfully!")
            
            # Ask user if they want to run tests
            print("\n" + "="*60)
            print("🤖 AI-Enhanced SAR System is running!")
            print("="*60)
            print("🌐 Backend: http://localhost:8000")
            print("🎨 Frontend: http://localhost:3000")
            print("🤖 AI Decisions: http://localhost:3000/ai-decisions")
            print("📊 API Docs: http://localhost:8000/docs")
            print("="*60)
            print("\nPress Ctrl+C to stop the system")
            print("="*60)
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n🛑 Shutdown requested by user")
        
    except Exception as e:
        logger.error(f"❌ Failed to start system: {e}")
        return 1
    
    finally:
        starter.stop_system()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))