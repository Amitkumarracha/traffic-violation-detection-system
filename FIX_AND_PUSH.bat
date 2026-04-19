@echo off
REM Fix the push error and push to GitHub

echo.
echo ========================================
echo   FIXING AND PUSHING TO GITHUB
echo ========================================
echo.

echo [1/6] Checking git status...
git status

echo.
echo [2/6] Adding all files...
git add .

echo.
echo [3/6] Creating commit...
git commit -m "Complete YOLO training setup for traffic violation detection - 9 datasets, 7078 images, GPU optimized"

echo.
echo [4/6] Checking branch...
git branch

echo.
echo [5/6] Creating main branch if needed...
git branch -M main

echo.
echo [6/6] Pushing to GitHub...
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
    echo If you see "Authentication failed":
    echo   - Use Personal Access Token as password
    echo   - Get token from: https://github.com/settings/tokens
    echo.
    echo If you see "rejected":
    echo   - Run: git pull origin main --allow-unrelated-histories
    echo   - Then run this script again
    echo.
)

pause
