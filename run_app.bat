@echo off
REM run_app.bat - Start FlexDeploy UI and Server simultaneously (Windows)

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo                     FlexDeploy Launcher
echo           AI-Powered Deployment Orchestrator
echo ================================================================
echo.

REM Check if config.ini exists
if not exist "config.ini" (
    echo [ERROR] config.ini not found!
    echo.
    echo Please run setup first:
    echo   setup_config.bat
    exit /b 1
)

REM Check if AWS credentials exist
if not exist "%USERPROFILE%\.aws\credentials" (
    echo [WARNING] AWS credentials not found at %USERPROFILE%\.aws\credentials
    echo AI features will be disabled.
    echo.
)

REM Check if server database exists
if not exist "server\flexdeploy.db" (
    echo [WARNING] Database not found. Creating new database...
)

REM Start Backend Server
echo [1/2] Starting Backend Server...
echo --------------------------------------

start /b cmd /c "python -m server.main > server.log 2>&1"
echo [OK] Server started
echo   Logs: server.log
echo   URL: http://localhost:8000
echo.

REM Wait for server to be ready
echo Waiting for server to be ready...
set MAX_RETRIES=30
set RETRY_COUNT=0

:wait_server
if !RETRY_COUNT! geq %MAX_RETRIES% (
    echo [ERROR] Server failed to start within 30 seconds
    type server.log | more +1000
    exit /b 1
)

curl -s http://localhost:8000/ >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Server is ready!
    goto server_ready
)

echo|set /p=.
timeout /t 1 /nobreak >nul
set /a RETRY_COUNT+=1
goto wait_server

:server_ready
echo.

REM Start Frontend UI
echo [2/2] Starting Frontend UI...
echo --------------------------------------

cd ui
start /b cmd /c "npm run dev > ..\ui.log 2>&1"
cd ..

echo [OK] UI started
echo   Logs: ui.log
echo   URL: http://localhost:5173
echo.

REM Wait for UI to be ready
echo Waiting for UI to be ready...
timeout /t 3 /nobreak >nul
echo [OK] UI is ready!

echo.
echo ================================================================
echo           [OK] FlexDeploy is running successfully!
echo ================================================================
echo.
echo Services:
echo   [OK] Backend:  http://localhost:8000
echo   [OK] Frontend: http://localhost:5173
echo   [OK] API Docs: http://localhost:8000/docs
echo.
echo Logs:
echo   Server: type server.log
echo   UI:     type ui.log
echo.
echo Press Ctrl+C to stop both services
echo.

REM Keep script running
:loop
timeout /t 2 /nobreak >nul

REM Check if server is still running
netstat -ano | findstr ":8000" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Server process died unexpectedly
    echo Check server.log for errors:
    type server.log | more +1000
    goto cleanup
)

REM Check if UI is still running
netstat -ano | findstr ":5173" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] UI process died unexpectedly
    echo Check ui.log for errors:
    type ui.log | more +1000
    goto cleanup
)

goto loop

:cleanup
echo.
echo Shutting down FlexDeploy...

REM Kill processes on ports 8000 and 5173
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [OK] FlexDeploy stopped

endlocal
