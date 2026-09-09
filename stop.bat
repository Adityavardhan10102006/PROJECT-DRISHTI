@echo off
REM Project DRISHTI - Windows Safe Stop Script
title PROJECT DRISHTI - Stopping Services...

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
) else (
    set "PY_CMD=py"
)

if exist ".venv\Scripts\python.exe" (
    set "DRISHTI_PYTHON=.venv\Scripts\python.exe"
) else (
    set "DRISHTI_PYTHON=%PY_CMD%"
)

"%DRISHTI_PYTHON%" scripts\stop.py %*
