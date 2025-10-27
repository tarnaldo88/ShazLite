@echo off
REM Windows deployment script for Audio Fingerprinting System
REM This is a wrapper for the bash script - requires WSL or Git Bash

echo Audio Fingerprinting System - Windows Deployment
echo.

REM Check if WSL is available
wsl --version >nul 2>&1
if %errorlevel% == 0 (
    echo Using WSL to run deployment script...
    wsl bash ./scripts/deploy.sh %*
) else (
    REM Check if Git Bash is available
    where bash >nul 2>&1
    if %errorlevel% == 0 (
        echo Using Git Bash to run deployment script...
        bash ./scripts/deploy.sh %*
    ) else (
        echo Error: Neither WSL nor Git Bash found.
        echo Please install WSL or Git for Windows to run the deployment script.
        echo.
        echo Alternative: Use Docker Desktop and run:
        echo   docker-compose up -d
        pause
        exit /b 1
    )
)

pause