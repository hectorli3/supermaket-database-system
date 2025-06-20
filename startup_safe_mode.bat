@echo off
title Supermarket System - Safe Mode Launcher

echo ==========================================================
echo = Supermarket Management System - Safe Mode Launcher     =
echo ==========================================================
echo.
echo This script will start the backend and frontend servers.
echo It uses only standard English characters to avoid encoding issues.
echo.

REM --- Step 1: Check for Python ---
echo [1/5] Checking for Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found!
    echo Please install Python 3.8+ and add it to your system's PATH.
    goto :error_exit
)
echo [OK] Python check passed.
echo.

REM --- Step 2: Check Python dependencies ---
echo [2/5] Checking Python dependencies...
pip show flask >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Python dependencies might be missing. Attempting to install...
    pip install -r requirements.txt -q
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install Python dependencies.
        echo Please run 'pip install -r requirements.txt' manually in this window.
        goto :error_exit
    )
)
echo [OK] Python dependencies are installed.
echo.

REM --- Step 3: Check for Node.js ---
echo [3/5] Checking for Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not found!
    echo Please download and install Node.js from https://nodejs.org
    goto :error_exit
)
echo [OK] Node.js check passed.
echo.

REM --- Step 4: Check frontend dependencies ---
echo [4/5] Checking frontend dependencies (node_modules)...
set "FRONTEND_DIR=%~dp0supermarket-frontend"
if not exist "%FRONTEND_DIR%\node_modules" (
    echo [WARNING] Frontend dependencies are not installed. Running 'npm install'...
    echo This may take a few minutes. Please wait.
    cd /d "%FRONTEND_DIR%"
    npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install frontend dependencies.
        echo Please manually navigate to the 'supermarket-frontend' directory and run 'npm install'.
        cd /d "%~dp0"
        goto :error_exit
    )
    cd /d "%~dp0"
)
echo [OK] Frontend dependencies are installed.
echo.

REM --- Step 5: Start Servers ---
echo [5/5] Starting servers...
echo Two new windows will be opened for the backend and frontend.
echo Do not close these new windows.
echo.

REM Start Backend Server
echo Starting backend server (on port 5000)...
start "Backend Server - Flask" cmd /k "title Backend Server (Flask) & python complete_server.py"

echo Waiting for backend to initialize (5 seconds)...
timeout /t 5 /nobreak >nul
echo.

REM Start Frontend Server
echo Starting frontend server (on port 3000)...
start "Frontend Server - Vue" cmd /k "cd /d "%FRONTEND_DIR%" & title Frontend Dev Server (Vue) & npm run dev"

echo Waiting for frontend to compile (8 seconds)...
timeout /t 8 /nobreak >nul
echo.

echo ==========================================================
echo =                    LAUNCH SUCCESSFUL                     =
echo ==========================================================
echo.
echo - Services are running in separate windows.
echo - Frontend URL: http://localhost:3000
echo - Backend URL:  http://localhost:5000
echo.
echo - To stop the system, simply close the two new windows.
echo.

set /p choice="Do you want to open the frontend in a browser now? (Y/N): "
if /i "%choice%"=="Y" (
    echo Opening browser...
    start http://localhost:3000
)

echo.
echo This window will close in 15 seconds.
timeout /t 15 >nul
exit /b 0

:error_exit
echo.
echo ==========================================================
echo =                       LAUNCH FAILED                      =
echo ==========================================================
echo.
echo Please check the error message above and try to fix it.
echo.
pause
exit /b 1 