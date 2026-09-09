@echo off
REM Project DRISHTI - Windows One-Click Fast Startup Launcher
title PROJECT DRISHTI - Launching...

REM 1. Locate Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_SYSTEM=python"
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PY_SYSTEM=py"
    ) else (
        echo [ERROR] Python 3.9+ was not found on your system PATH.
        echo         Please install Python and rerun setup.bat.
        pause
        exit /b 1
    )
)

REM 2. Check or select Python executable (use .venv if present)
if exist ".venv\Scripts\python.exe" (
    set "DRISHTI_PYTHON=.venv\Scripts\python.exe"
) else (
    if exist "venv\Scripts\python.exe" (
        set "DRISHTI_PYTHON=venv\Scripts\python.exe"
    ) else (
        set "DRISHTI_PYTHON=%PY_SYSTEM%"
    )
)

REM 3. If node_modules missing, run npm install once
if not exist "frontend\node_modules" (
    echo [DRISHTI] First-time frontend dependency detection...
    where npm >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        cd frontend
        call npm install
        cd ..
    ) else (
        echo [WARN] npm not detected. Frontend dev server might not launch.
    )
)

REM 4. Execute start.py launcher with arguments
"%DRISHTI_PYTHON%" start.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Application exited with code %ERRORLEVEL%.
    pause
)
