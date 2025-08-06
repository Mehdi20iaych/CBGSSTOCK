@echo off
REM 🚀 Local Development Startup Script for Windows

echo 🏠 Starting Inventory Management System Locally
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3 is required but not installed. Please install Python 3.9+ from https://python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is required but not installed. Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo.
echo 📁 Setting up Backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt

REM Copy environment file
if not exist ".env" (
    copy .env.local .env
    echo ✅ Created backend/.env file
)

echo.
echo 📁 Setting up Frontend...
cd ..\frontend

REM Install dependencies
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    where yarn >nul 2>&1
    if %errorlevel% equ 0 (
        yarn install
    ) else (
        npm install
    )
)

REM Copy environment file
if not exist ".env" (
    copy .env.local .env
    echo ✅ Created frontend/.env file
)

echo.
echo 🎉 Setup Complete!
echo.
echo To start the application:
echo.
echo 1️⃣  Backend (in one terminal):
echo    cd backend
echo    venv\Scripts\activate
echo    uvicorn server:app --reload --host 0.0.0.0 --port 8001
echo.
echo 2️⃣  Frontend (in another terminal):
echo    cd frontend
echo    npm start  (or yarn start)
echo.
echo 3️⃣  Access the application:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8001
echo    API Docs: http://localhost:8001/docs
echo.
echo 📝 Make sure MongoDB is running or update MONGO_URL in backend/.env
pause