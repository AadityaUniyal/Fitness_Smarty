@echo off
REM Fitness Smarty AI Setup Script for Windows

echo 🚀 Setting up Fitness Smarty AI...

REM Backend Setup
echo.
echo 📦 Setting up Backend...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    (
        echo DATABASE_URL=sqlite:///./smarty_neural_core.db
        echo SECRET_KEY=your-secret-key-here-change-in-production
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=30
    ) > .env
    echo ✅ .env file created - Please update SECRET_KEY in production
)

REM Run migrations
echo Running database migrations...
python migrations\create_enhanced_schema.py

cd ..

REM Frontend Setup
echo.
echo 📦 Setting up Frontend...
cd frontend

REM Install dependencies
echo Installing Node dependencies...
call npm install

cd ..

echo.
echo ✅ Setup complete!
echo.
echo To start the application:
echo   Backend:  cd backend ^&^& venv\Scripts\activate ^&^& python main.py
echo   Frontend: cd frontend ^&^& npm run dev
echo.
echo API Documentation: http://localhost:8000/docs
echo Frontend: http://localhost:5173

pause
