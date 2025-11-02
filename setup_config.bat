@echo off
REM setup_config.bat - Setup FlexDeploy configuration files for Windows

setlocal enabledelayedexpansion

echo =================================
echo 🔧 FlexDeploy Configuration Setup
echo ==================================
echo.

REM Check if config.ini already exists
if exist config.ini (
    echo ⚠️  config.ini already exists!
    set /p overwrite="Do you want to overwrite it? (y/n) "
    if /i not "!overwrite!"=="y" (
        echo Keeping existing config.ini
        exit /b 0
    )
)

REM Copy example config
echo 📝 Creating config.ini from template...
copy config.ini.example config.ini >nul 2>&1
if errorlevel 1 (
    echo ❌ Failed to create config.ini
    exit /b 1
)
echo ✓ config.ini created
echo.

REM Prompt for SSO configuration
echo AWS SSO Configuration
echo ---------------------
set /p sso_url="SSO Start URL [https://superopsglobalhackathon.awsapps.com/start/#]: "
if "!sso_url!"=="" set sso_url=https://superopsglobalhackathon.awsapps.com/start/#

set /p sso_region="SSO Region [us-east-2]: "
if "!sso_region!"=="" set sso_region=us-east-2

REM Update config.ini using PowerShell for better text manipulation
powershell -Command "(Get-Content config.ini) -replace 'sso_start_url = .*', 'sso_start_url = !sso_url!' | Set-Content config.ini"
powershell -Command "(Get-Content config.ini) -replace 'sso_region = .*', 'sso_region = !sso_region!' | Set-Content config.ini"

echo ✓ SSO configuration saved to config.ini
echo.

REM Check for AWS credentials
echo AWS Credentials Check
echo ---------------------
set aws_creds=%USERPROFILE%\.aws\credentials

if exist "!aws_creds!" (
    echo ✓ %USERPROFILE%\.aws\credentials file exists
    
    findstr /C:"aws_access_key_id" "!aws_creds!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ Credentials appear to be configured
    ) else (
        echo ⚠️  %USERPROFILE%\.aws\credentials exists but may be empty
    )
) else (
    echo ❌ %USERPROFILE%\.aws\credentials not found
    echo.
    echo You need to create %USERPROFILE%\.aws\credentials with:
    echo.
    echo   [default]
    echo   aws_access_key_id = YOUR_KEY
    echo   aws_secret_access_key = YOUR_SECRET
    echo   aws_session_token = YOUR_TOKEN
    echo.
    set /p create_creds="Create %USERPROFILE%\.aws\credentials now? (y/n) "
    if /i "!create_creds!"=="y" (
        if not exist "%USERPROFILE%\.aws" mkdir "%USERPROFILE%\.aws"
        (
            echo [default]
            echo aws_access_key_id = YOUR_ACCESS_KEY_ID
            echo aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
            echo aws_session_token = YOUR_SESSION_TOKEN
        ) > "!aws_creds!"
        echo ✓ Created %USERPROFILE%\.aws\credentials template
        echo ⚠️  You MUST edit this file with your actual credentials!
        echo.
        set /p open_editor="Open in editor now? (y/n) "
        if /i "!open_editor!"=="y" (
            notepad "!aws_creds!"
        )
    )
)

echo.
echo ==================================
echo ✓ Configuration Setup Complete!
echo ==================================
echo.
echo Configuration files:
echo   ✓ config.ini - FlexDeploy settings (SSO, regions, models)
echo   ✓ %USERPROFILE%\.aws\credentials - AWS credentials (keys, tokens)
echo.
echo Next steps:
echo   1. Verify config.ini has correct SSO settings
echo   2. Update %USERPROFILE%\.aws\credentials with valid AWS credentials
echo   3. Run: deploy_bedrock.bat
echo.

endlocal
