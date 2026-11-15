@echo off
setlocal
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
cd /d "%ROOT%"

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher was not found.
    exit /b 1
)

py -3 "%ROOT%\src\build\build_exe.py"
if errorlevel 1 exit /b %errorlevel%

py -3 "%ROOT%\src\build\build_portable.py"
if errorlevel 1 exit /b %errorlevel%

echo [SUCCESS] Studio and portable package build completed.
echo [OUTPUT] %ROOT%\dist
exit /b 0
