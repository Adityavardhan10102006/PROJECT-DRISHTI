@echo off
REM Project DRISHTI - First-Time Environment Setup Script
title PROJECT DRISHTI - First-Time Setup

echo =================================================================
echo  [DRISHTI] ===============================================
echo  [DRISHTI] PROJECT DRISHTI - First-Time Automated Setup
echo  [DRISHTI] Cybercrime Predictive Intelligence Platform (5D)
echo  [DRISHTI] ===============================================
echo =================================================================
echo.

REM 1. Detect Python
echo [1/8] Detecting Python...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python 3.9+ was not found on your system PATH.
        echo         Please install Python from https://www.python.org/downloads/
        echo         Ensure "Add Python to PATH" is checked during installation.
        pause
        exit /b 1
    )
    set "PY_CMD=py"
) else (
    set "PY_CMD=python"
)
%PY_CMD% --version
echo [OK] Python detected.
echo.

REM 2. Detect Node.js and npm
echo [2/8] Detecting Node.js and npm...
where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js / npm was not found on your system PATH.
    echo         Please install Node.js (LTS version) from https://nodejs.org/
    echo         Ensure npm is added to your PATH, then re-run setup.bat.
    pause
    exit /b 1
)
call npm --version >nul 2>&1
echo [OK] Node.js and npm detected.
echo.

REM 3. Create Required Directories
echo [3/8] Creating required project directories...
if not exist "data" mkdir data
if not exist "models" mkdir models
if not exist "logs" mkdir logs
echo [OK] Directories verified (data, models, logs).
echo.

REM 4. Virtual Environment Setup
echo [4/8] Setting up Python virtual environment...
if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    %PY_CMD% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists (.venv).
)

if exist ".venv\Scripts\python.exe" (
    set "VENV_PYTHON=.venv\Scripts\python.exe"
    set "VENV_PIP=.venv\Scripts\pip.exe"
) else (
    set "VENV_PYTHON=%PY_CMD%"
    set "VENV_PIP=%PY_CMD% -m pip"
)
echo.

REM 5. Install Python Dependencies
echo [5/8] Installing Python dependencies (requirements.txt)...
call "%VENV_PIP%" install --upgrade pip --quiet
call "%VENV_PIP%" install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed successfully.
echo.

REM 6. Install Frontend Dependencies
echo [6/8] Installing React/Vite frontend dependencies (npm install)...
cd frontend
if not exist "node_modules" (
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install npm dependencies.
        cd ..
        pause
        exit /b 1
    )
    echo [OK] Frontend dependencies installed.
) else (
    echo [OK] Frontend node_modules already installed.
)
cd ..
echo.

REM 7. Initialize Database and Configuration
echo [7/8] Initializing database and configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [OK] Initialized .env from .env.example.
    )
)
call "%VENV_PYTHON%" -c "from backend.database import init_db; init_db()"
echo [OK] Database schema initialized.
echo.

REM 8. Validate ML Models and Pre-Flight Artifacts
echo [8/8] Checking pre-trained ML models and artifacts...
call "%VENV_PYTHON%" scripts\check_models.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Note: Pre-trained models are missing or corrupted.
    echo     Training all models offline now...
    call "%VENV_PYTHON%" -m backend.ml.train_all
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Offline training failed. Check output above.
        pause
        exit /b 1
    )
    echo [OK] All models trained and verified.
)

echo.
echo =================================================================
echo  [DRISHTI] SETUP COMPLETE!
echo  You only need to run setup.bat ONCE.
echo.
echo  To start PROJECT DRISHTI now or any time in the future, simply run:
echo      start.bat
echo =================================================================
echo.
pause
