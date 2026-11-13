@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"

echo [INFO] Starting KOF97 Mod Studio desktop GUI...
python "%ROOT_DIR%\src\studio\legacy_tk_gui.py"
if errorlevel 1 (
    echo [ERROR] KOF97 Mod Studio exited with error code %errorlevel%.
    pause
)
endlocal
