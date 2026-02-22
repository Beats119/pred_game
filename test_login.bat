@echo off
echo ========================================
echo   BDG WIN LOGIN TESTER
echo ========================================
echo.
echo Choose test mode:
echo   1. Visible Browser (watch it work!)
echo   2. Headless (background test)
echo.
set /p choice="Enter 1 or 2: "

if "%choice%"=="1" (
    echo.
    echo Starting visible browser test...
    echo Watch the browser window!
    echo.
    python test_login_visible.py
) else if "%choice%"=="2" (
    echo.
    echo Starting headless test...
    echo.
    python test_login_fixed.py
) else (
    echo Invalid choice!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Test Complete!
echo ========================================
echo.
echo Check logs/ folder for screenshots
echo.
pause
