@echo off
setlocal

echo 🍗 Welcome to Hope Kuku Shop Auto-Launcher (Windows)

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

:: Create Virtual Environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate Virtual Environment
call venv\Scripts\activate

:: Install dependencies
echo Syncing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

:: Create .env from example
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Warning: Default development settings loaded. Please update .env for production.
)

:: Ensure instance directory exists
if not exist instance mkdir instance

:: Launch the application
echo 🚀 Launching Hope Kuku Shop...
python app.py

pause
