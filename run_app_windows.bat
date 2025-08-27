@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Change to script directory (repo root)
cd /d "%~dp0"

echo === Checking prerequisites ===
where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js is required. Please install from https://nodejs.org and retry.
  pause
  exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm is required. Please install Node.js (includes npm) and retry.
  pause
  exit /b 1
)

REM Prefer Python launcher
set PYTHON_EXE=
where py >nul 2>&1 && set PYTHON_EXE=py -3
if "%PYTHON_EXE%"=="" (
  where python >nul 2>&1 && set PYTHON_EXE=python
)
if "%PYTHON_EXE%"=="" (
  echo [ERROR] Python 3 is required. Please install from https://www.python.org/downloads/ and retry.
  pause
  exit /b 1
)

echo === Creating Python virtual environment (.venv) if missing ===
if not exist .venv\Scripts\python.exe (
  %PYTHON_EXE% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create virtualenv. Ensure Python 3 is installed.
    pause
    exit /b 1
  )
)

echo === Activating virtual environment ===
call .venv\Scripts\activate
if errorlevel 1 (
  echo [ERROR] Failed to activate virtualenv.
  pause
  exit /b 1
)

echo === Upgrading pip ===
python -m pip install --upgrade pip

echo === Installing backend dependencies ===
pip install -r backend\requirements.txt
if errorlevel 1 (
  echo [ERROR] Pip install failed. Check your internet connection.
  pause
  exit /b 1
)

echo === Installing JavaScript dependencies ===
npm install
if errorlevel 1 (
  echo [ERROR] npm install failed at root.
  pause
  exit /b 1
)

echo === Installing frontend dependencies ===
npm run install-frontend
if errorlevel 1 (
  echo [ERROR] npm install failed in frontend.
  pause
  exit /b 1
)

echo === Building frontend ===
npm run build
if errorlevel 1 (
  echo [ERROR] Frontend build failed.
  pause
  exit /b 1
)

echo === Launching desktop app ===
set BACKEND_PORT=8001
npx electron .

endlocal
