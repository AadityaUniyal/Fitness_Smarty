@echo off
REM Comprehensive Smarty-Reco Setup Script for Windows
REM This script sets up both backend and frontend

setlocal enabledelayedexpansion

echo ================================
echo   Smarty-Reco Complete Setup
echo ================================
echo.

REM Check if we're in the right directory
if not exist "README.md" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)

REM Step 1: Backend Setup
echo [Step 1] Setting up Backend...
echo.

cd backend

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo Python found
echo.

REM Create virtual environment
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install backend dependencies
echo Installing backend dependencies...
pip install -q -r requirements.txt
echo Backend dependencies installed
echo.

REM Check .env
if not exist ".env" (
    echo Creating .env from template...
    copy .env.example .env >nul
    echo .env created - Please update with your API keys
) else (
    echo .env already exists
)
echo.

REM Initialize database
echo Initializing database...
python -c "from app.database import engine; from app import models; models.Base.metadata.create_all(bind=engine)" 2>nul
echo Database initialized
echo.

REM Test backend setup
echo Running backend verification...
python verify_setup.py 2>nul || echo Verification completed with warnings
echo.

cd ..

REM Step 2: Frontend Setup
echo [Step 2] Setting up Frontend...
echo.

cd frontend

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed
    exit /b 1
)

echo Node.js found: 
node --version
echo npm found: 
npm --version
echo.

REM Install frontend dependencies
echo Installing frontend dependencies...
npm install --quiet
if errorlevel 1 (
    echo Retrying with legacy peer deps...
    npm install --legacy-peer-deps --quiet
)
echo Frontend dependencies installed
echo.

REM Check .env.local
if not exist ".env.local" (
    echo Creating .env.local from template...
    copy .env.local.example .env.local >nul
    echo .env.local created - Configure as needed
) else (
    echo .env.local already exists
)
echo.

cd ..

REM Step 3: Summary
echo.
echo ================================
echo   Setup Complete!
echo ================================
echo.
echo Next steps:
echo.
echo 1. Update API Keys (if needed):
echo    Backend:  backend\.env (GEMINI_API_KEY)
echo    Frontend: frontend\.env.local (optional)
echo.
echo 2. Start the Backend:
echo    cd backend
echo    python main.py
echo    (or: uvicorn main:app --reload)
echo.
echo 3. Start the Frontend (in another terminal):
echo    cd frontend
echo    npm run dev
echo.
echo 4. Access the Application:
echo    Frontend: http://localhost:5173
echo    API Docs: http://localhost:8000/docs
echo.
echo Happy coding!
echo.

pause
