@echo off

REM ====================================================
REM Smarty-reco Project Verification Script
REM ----------------------------------------------------
REM This script performs the following steps:
REM   1. Install backend Python dependencies
REM   2. Run backend unit tests
REM   3. Lint backend code (flake8) if installed
REM   4. Install frontend npm dependencies
REM   5. Lint and build the frontend
REM   6. Build and start Docker containers
REM   7. Show container status
REM ----------------------------------------------------
REM Prerequisites:
REM   - Python 3.x and pip in PATH
REM   - Node.js and npm in PATH
REM   - Docker Desktop running (docker compose available)
REM   - A .env file at project root (copy from .env.example if missing)
REM ====================================================

setlocal

REM ---------- Backend ----------
echo =============================
echo Installing backend dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies.
    exit /b 1
)

echo =============================
echo Running backend tests...
pytest -q
if errorlevel 1 (
    echo ERROR: Some backend tests failed.
    exit /b 1
)

REM Optional linting (requires flake8 or ruff)
where flake8 >nul 2>&1
if %errorlevel%==0 (
    echo =============================
    echo Linting backend with flake8...
    flake8 .
) else (
    echo flake8 not found, skipping backend lint.
)

REM ---------- Frontend ----------
pushd frontend

echo =============================
echo Installing frontend dependencies...
npm install
if errorlevel 1 (
    echo ERROR: npm install failed.
    popd
    exit /b 1
)

echo =============================
echo Linting frontend...
npm run lint
if errorlevel 1 (
    echo WARNING: Frontend linting reported issues.
)

echo =============================
echo Building frontend...
npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed.
    popd
    exit /b 1
)
popd

REM ---------- Docker ----------
echo =============================
echo Building Docker images...
docker compose build
if errorlevel 1 (
    echo ERROR: Docker build failed.
    exit /b 1
)

echo =============================
echo Starting Docker containers...
docker compose up -d
if errorlevel 1 (
    echo ERROR: Docker compose up failed.
    exit /b 1
)

echo =============================
echo Docker container status:
docker compose ps

echo =============================
echo Verification script completed successfully.
pause
endlocal
