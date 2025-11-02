@echo off
REM install.bat - First-time setup for FlexDeploy (Windows)

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo               FlexDeploy Installation
echo        First-time setup for all dependencies
echo ================================================================
echo.

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11+ is required
    echo Install from: https://www.python.org/downloads/
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Check Node.js
echo.
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js 18+ is required
    echo Install from: https://nodejs.org/
    exit /b 1
)
for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo [OK] Node.js %NODE_VERSION% found

REM Check/Install uv
echo.
echo [3/6] Checking uv package manager...
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing uv...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo [WARNING] uv installation failed, using pip instead
        set USE_UV=0
    ) else (
        echo [OK] uv installed
        set USE_UV=1
    )
) else (
    echo [OK] uv already installed
    set USE_UV=1
)

REM Install Python packages
echo.
echo [4/6] Installing Python packages...
if !USE_UV! equ 1 (
    uv pip install -e .
) else (
    pip install -e .
)
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python packages
    exit /b 1
)
echo [OK] Python packages installed
echo   - fastapi, uvicorn
echo   - boto3, botocore
echo   - strands-agents
echo   - aiohttp, asyncio

REM Install npm packages
echo.
echo [5/6] Installing npm packages...
cd ui
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install npm packages
    cd ..
    exit /b 1
)
cd ..
echo [OK] npm packages installed
echo   - react, react-router-dom
echo   - @mui/material, @mui/icons-material
echo   - recharts
echo   - vite

REM Setup configuration
echo.
echo [6/6] Setting up configuration...
if not exist "config.ini" (
    echo Running configuration setup...
    call setup_config.bat
) else (
    echo [WARNING] config.ini already exists, skipping setup
)

REM Summary
echo.
echo ================================================================
echo           [OK] Installation completed successfully!
echo ================================================================
echo.
echo What was installed:
echo   [OK] Python packages (backend dependencies)
echo   [OK] npm packages (frontend dependencies)
echo   [OK] uv package manager
echo   [OK] Configuration files
echo.
echo Next steps:
echo.
echo 1. Configure AWS credentials:
echo    Create/edit: %USERPROFILE%\.aws\credentials
echo.
echo    Add your AWS credentials:
echo    [default]
echo    aws_access_key_id = YOUR_KEY
echo    aws_secret_access_key = YOUR_SECRET
echo    aws_session_token = YOUR_TOKEN  # If using SSO
echo.
echo 2. Enable AWS Bedrock model access:
echo    - Login to AWS Console
echo    - Go to AWS Bedrock -^> Model access
echo    - Request access to Amazon Nova Pro ^& Lite
echo.
echo 3. Test Bedrock connection:
echo    python test_bedrock_agents.py
echo.
echo 4. Start the application:
echo    run_app.bat
echo.
echo 5. Open in browser:
echo    http://localhost:5173
echo.
echo For more details, see: README.md
echo.

endlocal
