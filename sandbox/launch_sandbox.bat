@echo off
setlocal
cd /d "%~dp0"

set "TARGET_ROM=%~1"
if "%TARGET_ROM%"=="" set "TARGET_ROM=kof97pls"

if not exist "..\output\roms\kof97pls.zip" (
    echo [ERROR] Missing ..\output\roms\kof97pls.zip. Run tools\rom_tool.py build-baseline first.
    exit /b 1
)

echo [INFO] Launching WinKawaks 1.48 sandbox with ROM set: %TARGET_ROM%
echo [INFO] RomPath1 = ..\output\roms
echo [INFO] RomPath2 = C:\Program Files (x86)\KOF97\roms
python "..\tools\rom_tool.py" launch-sandbox %TARGET_ROM%
if errorlevel 1 (
    start "" "%~dp0WinKawaks.exe" %TARGET_ROM%
)
endlocal
