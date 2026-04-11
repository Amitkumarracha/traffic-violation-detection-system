@echo off
REM Quick push to GitHub - Run this file!

echo.
echo ========================================
echo   PUSHING TO GITHUB
echo ========================================
echo.
echo Repository: https://github.com/Amitkumarracha/traffic-violation-detection-system.git
echo.
echo This will:
echo   1. Initialize git (if needed)
echo   2. Add all files
echo   3. Commit changes
echo   4. Push to GitHub
echo.
pause

echo.
echo [1/5] Initializing git...
git init

echo.
echo [2/5] Adding remote...
git remote add origin https://github.com/Amitkumarracha/traffic-violation-detection-system.git 2>nul
if %ERRORLEVEL% NEQ 0 (
    git remote set-url origin https://github.com/Amitkumarracha/traffic-violation-detection-system.git
)

echo.
echo [3/5] Adding files...
git add .

echo.
echo [4/5] Committing...
git commit -m "Complete YOLO training setup for traffic violation detection - 9 datasets, 7078 images, GPU optimized"

echo.
echo [5/5] Pushing to GitHub...
git branch -M main
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   ✅ SUCCESS!
    echo ========================================
    echo.
    echo Your project is now on GitHub:
    echo https://github.com/Amitkumarracha/traffic-violation-detection-system
    echo.
) else (
    echo.
    echo ========================================
    echo   ⚠️ PUSH FAILED
    echo ========================================
    echo.
    echo Possible solutions:
    echo.
    echo 1. If repository has existing content:
    echo    git pull origin main --allow-unrelated-histories
    echo    git push -u origin main
    echo.
    echo 2. If authentication failed:
    echo    - Use GitHub Personal Access Token
    echo    - Or use SSH key
    echo    - Or use GitHub Desktop
    echo.
    echo 3. If branch doesn't exist:
    echo    git push -u origin master
    echo.
)

pause
