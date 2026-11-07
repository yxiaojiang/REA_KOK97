@echo off
setlocal
cd /d "%~dp0"

echo [INFO] Starting KOF97 Mod Studio Desktop GUI...
python tools\kof97_gui.py
if errorlevel 1 (
    echo [ERROR] KOF97 Mod Studio exited with error code %errorlevel%.
    pause
)
endlocal
