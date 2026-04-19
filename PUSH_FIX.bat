@echo off
REM Fix: Push to correct branch

echo.
echo ========================================
echo   PUSHING TO GITHUB (FIXED)
echo ========================================
echo.

echo Current branch:
git branch

echo.
echo Renaming branch to 'main'...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   ✅ SUCCESS!
    echo ========================================
    echo.
    echo Repository: https://github.com/Amitkumarracha/traffic-violation-detection-system
    echo.
) else (
    echo.
    echo ========================================
    echo   ⚠️ STILL HAVING ISSUES?
    echo ========================================
    echo.
    echo Try pushing to master branch instead:
    echo   git push -u origin master
    echo.
    echo Or if authentication failed:
    echo   - Use Personal Access Token as password
    echo   - Get from: https://github.com/settings/tokens
    echo.
)

pause
