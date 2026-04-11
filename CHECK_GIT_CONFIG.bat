@echo off
REM Check Git Configuration

echo.
echo ========================================
echo   GIT CONFIGURATION
echo ========================================
echo.

echo Checking Git username...
git config user.name
if %ERRORLEVEL% NEQ 0 (
    echo   ⚠️  Username not set
) else (
    echo.
)

echo Checking Git email...
git config user.email
if %ERRORLEVEL% NEQ 0 (
    echo   ⚠️  Email not set
) else (
    echo.
)

echo ========================================
echo   ALL GIT SETTINGS
echo ========================================
echo.
git config --list | findstr "user"

echo.
echo ========================================
echo   TO SET USERNAME AND EMAIL
echo ========================================
echo.
echo git config --global user.name "Your Name"
echo git config --global user.email "your.email@example.com"
echo.

pause
