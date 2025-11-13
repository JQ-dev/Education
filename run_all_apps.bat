@echo off
REM Run all three SABER dashboard applications in parallel
REM Each runs on a different port

echo ========================================
echo Starting SABER Dashboard Applications
echo ========================================
echo.
echo App 1: Basic Dashboard      - http://127.0.0.1:8051/
echo App 2: Government Analytics - http://127.0.0.1:8052/
echo App 3: Temporal Analysis    - http://127.0.0.1:8053/
echo.
echo Press Ctrl+C to stop all apps
echo ========================================
echo.

REM Start all three apps in separate windows
start "SABER Basic" cmd /k "python app.py"
timeout /t 2 /nobreak >nul
start "SABER Enhanced" cmd /k "python app_enhanced.py"
timeout /t 2 /nobreak >nul
start "SABER Temporal" cmd /k "python app_temporal.py"

echo.
echo All apps started!
echo Close this window or press any key to exit...
pause >nul
