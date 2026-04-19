@echo off
echo ============================================================
echo   Traffic Violation Detection - Full System with Camera
echo ============================================================
echo.

echo [1/4] Starting Backend API Server...
echo.
start "Backend API" cmd /k "uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul

echo [2/4] Opening Frontend Dashboard...
echo.
start http://localhost:8000
timeout /t 2 /nobreak >nul

echo [3/4] Starting Webcam Detection...
echo.
timeout /t 3 /nobreak >nul
start "Webcam Detection" cmd /k "python examples/demos/demo_webcam.py"

echo [4/4] System Ready!
echo.
echo ============================================================
echo   FULL SYSTEM STARTED
echo ============================================================
echo.
echo   Frontend:  http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   Camera:    Running in separate window
echo.
echo   Press 'q' in camera window to stop detection
echo   Press Ctrl+C in Backend window to stop server
echo.
echo ============================================================
echo.
echo Press any key to exit this window...
pause >nul
