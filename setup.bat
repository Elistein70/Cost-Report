@echo off
REM ClearDOH Setup Script for Windows

echo.
echo 🚀 ClearDOH Setup Script
echo ========================
echo.

REM Check Python
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install from https://python.org
    pause
    exit /b 1
)
echo ✅ Python found

REM Check Node
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install from https://nodejs.org
    pause
    exit /b 1
)
echo ✅ Node.js found

REM Setup Backend
echo.
echo Setting up backend...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate and install
echo Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -q -r requirements.txt

REM Create .env
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
)

REM Create directories
if not exist "uploads" mkdir uploads
if not exist "output" mkdir output
if not exist "templates" mkdir templates
if not exist "data" mkdir data

echo ✅ Backend setup complete!

cd ..

REM Setup Frontend
echo.
echo Setting up frontend...
cd frontend

echo Installing Node dependencies (this may take a few minutes)...
call npm install

echo ✅ Frontend setup complete!

cd ..

echo.
echo 🎉 Setup Complete!
echo.
echo To run ClearDOH:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   venv\Scripts\activate
echo   python -m uvicorn main:app --reload
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Then open: http://localhost:3000
echo.
pause
