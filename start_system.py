#!/usr/bin/env python3
"""
SAR Drone Swarm System - Single Command Startup
Runs all services in one process with proper cleanup
"""

import subprocess
import sys
import os
import time
import requests
import signal
import threading
from pathlib import Path

class SARSystemManager:
    def __init__(self):
        self.processes = []
        self.threads = []
        self.running = True
        
    def log(self, message: str, level: str = "INFO"):
        """Log startup messages"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def check_port(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def check_frontend_port(self, port: int) -> bool:
        """Check if frontend port is available"""
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def start_ollama(self):
        """Start Ollama service"""
        def run_ollama():
            try:
                subprocess.run(["ollama", "serve"], check=True)
            except subprocess.CalledProcessError:
                self.log("Ollama not found or failed to start", "WARNING")
            except FileNotFoundError:
                self.log("Ollama not installed. Please install Ollama first.", "WARNING")
        
        ollama_thread = threading.Thread(target=run_ollama, daemon=True)
        ollama_thread.start()
        time.sleep(3)  # Give Ollama time to start
        
        # Check if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                self.log(f"✅ Ollama service started with {len(models)} models")
                return True
        except:
            pass
            
        self.log("⚠️  Ollama service not available - AI features may be limited", "WARNING")
        return False
    
    def start_backend(self):
        """Start the backend server"""
        def run_backend():
            backend_dir = Path("backend")
            try:
                # Initialize database
                subprocess.run([sys.executable, "init_db.py"], cwd=backend_dir, check=True)
                
                # Start backend server
                subprocess.run([
                    sys.executable, "-m", "uvicorn", 
                    "app.main:app", 
                    "--reload", 
                    "--host", "0.0.0.0", 
                    "--port", "8000"
                ], cwd=backend_dir)
            except Exception as e:
                self.log(f"Backend error: {e}", "ERROR")
        
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        backend_thread.start()
        self.threads.append(backend_thread)
        
        # Wait for backend to start
        for i in range(30):
            if self.check_port(8000):
                self.log("✅ Backend server started on port 8000")
                return True
            time.sleep(1)
        
        self.log("❌ Backend server failed to start", "ERROR")
        return False
    
    def start_frontend(self):
        """Start the frontend server"""
        def run_frontend():
            frontend_dir = Path("frontend")
            try:
                # Install dependencies if needed
                if not (frontend_dir / "node_modules").exists():
                    subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                
                # Start frontend server
                subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)
            except Exception as e:
                self.log(f"Frontend error: {e}", "ERROR")
        
        frontend_thread = threading.Thread(target=run_frontend, daemon=True)
        frontend_thread.start()
        self.threads.append(frontend_thread)
        
        # Wait for frontend to start
        for i in range(60):  # Frontend takes longer to start
            if self.check_frontend_port(3000):
                self.log("✅ Frontend server started on port 3000")
                return True
            time.sleep(1)
        
        self.log("❌ Frontend server failed to start", "ERROR")
        return False
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log("🛑 Shutdown signal received...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up all processes and threads"""
        self.log("🧹 Cleaning up processes and threads...")
        
        # Clean up threads (daemon threads will exit automatically)
        for thread in self.threads:
            if thread.is_alive():
                self.log(f"Thread {thread.name} still running (daemon will exit)")
        
        # Clean up any remaining processes
        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        
        self.log("✅ Cleanup complete")
    
    def run(self):
        """Run the complete system"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🚁 SAR Drone Swarm System - Single Command Startup")
        print("=" * 60)
        
        # Start Ollama
        self.log("🤖 Starting Ollama AI service...")
        ollama_ok = self.start_ollama()
        
        # Start backend
        self.log("🔧 Starting backend server...")
        backend_ok = self.start_backend()
        if not backend_ok:
            self.log("Failed to start backend. Exiting.", "ERROR")
            self.cleanup()
            return 1
        
        # Start frontend
        self.log("🎨 Starting frontend server...")
        frontend_ok = self.start_frontend()
        if not frontend_ok:
            self.log("Failed to start frontend. Exiting.", "ERROR")
            self.cleanup()
            return 1
        
        # Final status
        print("\n" + "=" * 60)
        print("🎉 SAR Drone Swarm System Started Successfully!")
        print("=" * 60)
        print("✅ Backend: http://localhost:8000")
        print("✅ Frontend: http://localhost:3000")
        print("✅ API Docs: http://localhost:8000/docs")
        print("✅ Health Check: http://localhost:8000/health")
        
        if ollama_ok:
            print("✅ AI Service: Ollama running")
        else:
            print("⚠️  AI Service: Limited functionality (install Ollama)")
        
        print("\n🚁 System ready for SAR operations!")
        print("Press Ctrl+C to stop all services")
        print("=" * 60)
        
        # Keep running until interrupted
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
            print("\n✅ SAR Drone Swarm System shutdown complete")
        
        return 0

def main():
    """Main entry point"""
    manager = SARSystemManager()
    return manager.run()

if __name__ == "__main__":
    sys.exit(main())
