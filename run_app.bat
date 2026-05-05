@echo off
title VN Stock Daily Analysis
echo ==========================================
echo   VN STOCK DAILY ANALYSIS - STARTING...
echo ==========================================

:: Activate venv if exists
if exist "venv\Scripts\activate" (
    echo [0] Activating venv...
    call venv\Scripts\activate
)

:: Start Backend
echo [1] Launching Backend - http://localhost:8000
start "Backend" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak > nul

:: Start Frontend
echo [2] Launching Frontend - http://localhost:3000
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo   Done! Open http://localhost:3000
echo ==========================================
