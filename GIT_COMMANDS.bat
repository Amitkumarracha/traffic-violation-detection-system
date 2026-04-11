@echo off
REM Push project to GitHub

echo ========================================
echo Pushing to GitHub
echo ========================================
echo.
echo Repository: https://github.com/Amitkumarracha/traffic-violation-detection-system.git
echo.

REM Initialize git if needed
git init

REM Add remote
git remote add origin https://github.com/Amitkumarracha/traffic-violation-detection-system.git 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Remote already exists, updating URL...
    git remote set-url origin https://github.com/Amitkumarracha/traffic-violation-detection-system.git
)

REM Add all files
echo.
echo Adding files...
git add .

REM Commit
echo.
echo Committing changes...
git commit -m "Initial commit: YOLO training setup for traffic violation detection"

REM Push
echo.
echo Pushing to GitHub...
git branch -M main
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Successfully pushed to GitHub!
    echo ========================================
    echo.
    echo Repository: https://github.com/Amitkumarracha/traffic-violation-detection-system
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ Push failed!
    echo ========================================
    echo.
    echo Try these solutions:
    echo 1. Check your GitHub credentials
    echo 2. Make sure you have write access to the repository
    echo 3. Try: git pull origin main --allow-unrelated-histories
    echo 4. Then run this script again
    echo.
)

pause
