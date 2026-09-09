@echo off
REM Project DRISHTI - Easy One-Click Startup
title PROJECT DRISHTI
chcp 65001 >nul 2>&1

REM 1. Detect Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "DRISHTI_PY=python"
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "DRISHTI_PY=py"
    ) else (
        echo [ERROR] Python was not found on your system PATH.
        echo         Please install Python from https://python.org
        pause
        exit /b 1
    )
)

REM 2. Use virtual environment if present
if exist ".venv\Scripts\python.exe" (
    set "DRISHTI_PY=.venv\Scripts\python.exe"
) else (
    if exist "venv\Scripts\python.exe" (
        set "DRISHTI_PY=venv\Scripts\python.exe"
    )
)

REM 3. Run launcher (auto-heals missing packages and models)
"%DRISHTI_PY%" start.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [DRISHTI] Starting first-time setup...
    call setup.bat
)
