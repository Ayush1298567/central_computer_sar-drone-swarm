#!/usr/bin/env python3
"""
Local AI Setup Script
Sets up Ollama and downloads required models for the SAR system
"""

import subprocess
import sys
import time
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalAISetup:
    """Setup local AI models for the SAR system"""
    
    def __init__(self):
        self.ollama_host = "http://localhost:11434"
        self.required_models = [
            "llama3.2:3b",  # Main model for mission planning
            "llama3.2:1b",  # Fallback model for faster responses
        ]
        
    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"✅ Ollama is installed: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("❌ Ollama is not installed")
        return False
    
    def install_ollama(self) -> bool:
        """Install Ollama"""
        try:
            logger.info("📦 Installing Ollama...")
            
            # Detect OS and install accordingly
            import platform
            system = platform.system().lower()
            
            if system == "linux":
                # Install Ollama on Linux
                install_script = """
                curl -fsSL https://ollama.ai/install.sh | sh
                """
                result = subprocess.run(install_script, shell=True, check=True)
                
            elif system == "darwin":  # macOS
                # Install via Homebrew
                result = subprocess.run(["brew", "install", "ollama"], check=True)
                
            elif system == "windows":
                logger.error("❌ Windows installation not supported in this script")
                logger.info("Please download Ollama from: https://ollama.ai/download")
                return False
            
            else:
                logger.error(f"❌ Unsupported operating system: {system}")
                return False
            
            logger.info("✅ Ollama installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install Ollama: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Installation error: {e}")
            return False
    
    def start_ollama_service(self) -> bool:
        """Start Ollama service"""
        try:
            logger.info("🚀 Starting Ollama service...")
            
            # Start Ollama in background
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait for service to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ Ollama service is running")
                        return True
                except:
                    pass
                time.sleep(1)
            
            logger.error("❌ Ollama service failed to start")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start Ollama service: {e}")
            return False
    
    def check_model_available(self, model: str) -> bool:
        """Check if a model is available"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                return model in model_names
        except:
            pass
        return False
    
    def download_model(self, model: str) -> bool:
        """Download a model"""
        try:
            logger.info(f"📥 Downloading model: {model}")
            
            # Use ollama pull command
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Model {model} downloaded successfully")
                return True
            else:
                logger.error(f"❌ Failed to download {model}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout downloading {model}")
            return False
        except Exception as e:
            logger.error(f"❌ Error downloading {model}: {e}")
            return False
    
    def test_model(self, model: str) -> bool:
        """Test a model with a simple prompt"""
        try:
            logger.info(f"🧪 Testing model: {model}")
            
            test_prompt = "Hello, are you working?"
            
            result = subprocess.run(
                ["ollama", "run", model, test_prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"✅ Model {model} is working")
                return True
            else:
                logger.error(f"❌ Model {model} test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Model {model} test timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Model {model} test error: {e}")
            return False
    
    def setup_models(self) -> bool:
        """Setup all required models"""
        success = True
        
        for model in self.required_models:
            if self.check_model_available(model):
                logger.info(f"✅ Model {model} is already available")
                if not self.test_model(model):
                    logger.warning(f"⚠️ Model {model} is available but not working properly")
                    success = False
            else:
                logger.info(f"📥 Model {model} not found, downloading...")
                if not self.download_model(model):
                    logger.error(f"❌ Failed to download {model}")
                    success = False
                elif not self.test_model(model):
                    logger.error(f"❌ Downloaded {model} but it's not working")
                    success = False
        
        return success
    
    def create_env_file(self) -> bool:
        """Create .env file with local AI configuration"""
        try:
            env_content = """# Local AI Configuration
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b
FALLBACK_MODEL=llama3.2:1b
AI_MODEL_TIMEOUT=30

# Database
DATABASE_URL=sqlite:///./sar_drone.db

# Security
SECRET_KEY=your-secret-key-change-in-production-make-it-very-long-and-secure

# API
API_HOST=0.0.0.0
API_PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173

# WebSocket
WS_URL=ws://localhost:8000/ws

# Logging
LOG_LEVEL=INFO
DEBUG=True
"""
            
            env_file = Path(".env")
            with open(env_file, "w") as f:
                f.write(env_content)
            
            logger.info("✅ Created .env file with local AI configuration")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run complete setup"""
        logger.info("🤖 Setting up Local AI for SAR System")
        logger.info("=" * 50)
        
        # Step 1: Check if Ollama is installed
        if not self.check_ollama_installed():
            logger.info("📦 Ollama not found, installing...")
            if not self.install_ollama():
                logger.error("❌ Failed to install Ollama")
                return False
        
        # Step 2: Start Ollama service
        if not self.start_ollama_service():
            logger.error("❌ Failed to start Ollama service")
            return False
        
        # Step 3: Setup models
        if not self.setup_models():
            logger.error("❌ Failed to setup models")
            return False
        
        # Step 4: Create configuration
        if not self.create_env_file():
            logger.error("❌ Failed to create configuration")
            return False
        
        logger.info("=" * 50)
        logger.info("🎉 Local AI setup completed successfully!")
        logger.info("🚀 You can now start the SAR system with: python start_ai_system.py")
        logger.info("=" * 50)
        
        return True

def main():
    """Main function"""
    setup = LocalAISetup()
    
    try:
        success = setup.run_setup()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n🛑 Setup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())