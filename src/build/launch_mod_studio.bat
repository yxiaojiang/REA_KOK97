@echo off
rem KOF97 Mod Studio desktop launcher.
rem Resolves the project root from this script's build folder.
setlocal
for %%I in ("%~dp0..\..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"

if exist "%ROOT_DIR%\KOF97ModStudio.exe" (
    start "" "%ROOT_DIR%\KOF97ModStudio.exe"
    exit /b 0
)

if exist "%ROOT_DIR%\dist\KOF97ModStudio.exe" (
    start "" "%ROOT_DIR%\dist\KOF97ModStudio.exe"
    exit /b 0
)

python "%ROOT_DIR%\src\studio\kof97_webview_app.py"
exit /b 0
