@echo off
rem KOF97 Mod Studio Desktop Launcher
rem Adheres strictly to Rules.md ASCII specification.
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

if exist "%ROOT_DIR%KOF97ModStudio.exe" (
    start "" "%ROOT_DIR%KOF97ModStudio.exe"
    exit /b 0
)

if exist "%ROOT_DIR%dist\KOF97ModStudio.exe" (
    start "" "%ROOT_DIR%dist\KOF97ModStudio.exe"
    exit /b 0
)

python "%ROOT_DIR%tools\kof97_webview_app.py"
exit /b 0
