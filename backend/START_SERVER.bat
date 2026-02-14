@echo off
REM Windows Batch Script to Start Smarty Reco Backend
REM Just double-click this file to start!

echo.
echo ============================================================
echo   SMARTY RECO - Starting Backend Server
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Run the launcher
python start.py

pause
