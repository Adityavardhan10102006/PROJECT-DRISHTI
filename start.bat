@echo off
REM Project DRISHTI — Simple One-Click Startup
title PROJECT DRISHTI — Command Center
chcp 65001 >nul 2>&1

REM 1. Detect Python executable
set "DRISHTI_PY=python"
if exist ".venv\Scripts\python.exe" (
    set "DRISHTI_PY=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "DRISHTI_PY=venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        where py >nul 2>&1
        if errorlevel 1 (
            echo [ERROR] Python was not found on your system PATH.
            echo Please install Python 3.9+ from https://www.python.org/
            pause
            exit /b 1
        )
        set "DRISHTI_PY=py"
    )
)

REM 2. Run DRISHTI Launcher
"%DRISHTI_PY%" start.py %*
if errorlevel 1 (
    if not "%1"=="--help" (
        echo.
        echo [!] DRISHTI exited with an error. Check logs above.
        pause
    )
)
