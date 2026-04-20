@echo off
setlocal enabledelayedexpansion
title VN Stock Daily Analysis - Modern UI
echo ==========================================
echo   VN STOCK DAILY ANALYSIS - STARTING...
echo ==========================================

:: Step 0: Virtual Environment Detection
set VENV_PATH=
if exist "venv\Scripts\activate" set VENV_PATH=venv
if exist ".venv\Scripts\activate" set VENV_PATH=.venv

if not "%VENV_PATH%"=="" (
    echo [0/3] Activating Virtual Environment: %VENV_PATH%
    call %VENV_PATH%\Scripts\activate
) else (
    echo [0/3] No virtual environment detected. Using system python.
    echo Tip: Run 'python -m venv venv' to create one for better management.
)

:: Step 1: Check dependencies
echo [1/3] Checking dependencies...
pip install -r requirements.txt
cd frontend && npm install && cd ..

:: Step 2: Start Backend (FastAPI)
echo [2/3] Launching Backend API (Port 8000)...
start "Backend (FastAPI)" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait a moment for Backend to initialize
timeout /t 3 /nobreak > nul

:: Step 3: Start Frontend (Next.js)
echo [3/3] Launching Frontend UI (Port 3000)...
start "Frontend (Next.js)" cmd /k "cd frontend && npm run dev"

echo ==========================================
echo   SYSTEM STARTED SUCCESSFULLY!
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:3000/
echo ==========================================
pause
