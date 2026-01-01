@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo [*] Checking dependencies...
pip install -r requirements.txt -q

if %errorlevel% neq 0 (
    echo [X] Install failed! Check network or proxy.
    pause
    exit /b
)

echo [OK] Ready, launching...
python main.py
pause
