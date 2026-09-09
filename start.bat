@echo off
REM Project DRISHTI - Easy One-Click Startup
title PROJECT DRISHTI
chcp 65001 >nul 2>&1

REM 1. Detect system Python
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

REM 2. Prefer virtual environment ONLY if it is populated with packages
if exist ".venv\Scripts\uvicorn.exe" (
    set "DRISHTI_PY=.venv\Scripts\python.exe"
) else (
    if exist "venv\Scripts\uvicorn.exe" (
        set "DRISHTI_PY=venv\Scripts\python.exe"
    )
)

REM 3. Run launcher
"%DRISHTI_PY%" start.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [DRISHTI] Starting setup to resolve environment issues...
    call setup.bat
)
