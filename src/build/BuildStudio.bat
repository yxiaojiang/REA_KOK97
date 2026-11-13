@echo off
rem Build standalone KOF97ModStudio.exe with PyInstaller.
rem Output: dist\KOF97ModStudio.exe, then a copy at the project root.
setlocal
for %%I in ("%~dp0..\..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"

if not exist "%ROOT_DIR%\src\build\build_exe.py" (
    echo [ERROR] Missing src\build\build_exe.py
    exit /b 1
)

echo [INFO] Building KOF97ModStudio.exe
python "%ROOT_DIR%\src\build\build_exe.py"
if errorlevel 1 (
    echo [ERROR] Build failed with error code %errorlevel%.
    pause
    exit /b %errorlevel%
)

echo [INFO] Build finished.
echo [INFO] dist\KOF97ModStudio.exe
echo [INFO] KOF97ModStudio.exe
endlocal
exit /b 0
