@echo off
echo ============================================================
echo   Traffic Violation Detection System - Startup Script
echo ============================================================
echo.

echo [1/3] Starting Backend API Server...
echo.
start "Backend API" cmd /k "uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 5 /nobreak >nul

echo [2/3] Opening Frontend Dashboard...
echo.
start http://localhost:8000
timeout /t 2 /nobreak >nul

echo [3/3] System Ready!
echo.
echo ============================================================
echo   SYSTEM STARTED SUCCESSFULLY
echo ============================================================
echo.
echo   Frontend Dashboard: http://localhost:8000
echo   API Documentation:  http://localhost:8000/docs
echo   WebSocket Stream:   ws://localhost:8000/ws/live
echo.
echo ============================================================
echo.
echo To start webcam detection, run in a new terminal:
echo   python examples/demos/demo_webcam.py
echo.
echo Or run the full pipeline:
echo   python examples/demos/demo_main_pipeline.py --demo 1
echo.
echo Press any key to exit this window...
pause >nul
