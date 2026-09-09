@echo off
REM Project DRISHTI — Windows One-Click Batch Launcher
title PROJECT DRISHTI — Launching...
python start.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Application exited with error code %ERRORLEVEL%.
    pause
)
