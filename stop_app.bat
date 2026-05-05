@echo off
echo Stopping all dev processes...
taskkill /F /IM node.exe /T >nul 2>nul
taskkill /F /IM uvicorn.exe /T >nul 2>nul
:: Kill only uvicorn python, not all python
wmic process where "commandline like '%%uvicorn%%'" delete >nul 2>nul
echo Done. All dev servers stopped.
pause
