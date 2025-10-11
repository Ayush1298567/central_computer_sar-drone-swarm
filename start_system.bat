@echo off
echo 🚁 SAR Drone Swarm System - Windows Startup
echo ==========================================
echo.
echo Starting all services in one command...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

REM Start the system
echo 🚀 Launching SAR Drone Swarm System...
python start_system.py

echo.
echo 🛑 System shutdown complete.
pause
