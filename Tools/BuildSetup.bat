@echo off
setlocal
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "ISS=%ROOT%\src\build\KOF97Portable.iss"

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo [ERROR] Inno Setup 6 compiler ISCC.exe was not found.
    exit /b 1
)
if not exist "%ROOT%\dist\KOF97-Portable-20261115\studio.exe" (
    echo [ERROR] Portable package is missing. Run BuildStudio.bat first.
    exit /b 1
)

"%ISCC%" "%ISS%"
if errorlevel 1 exit /b %errorlevel%

echo [SUCCESS] Setup installer created.
echo [OUTPUT] %ROOT%\dist\Installer\KOF97-Mod-Studio-Setup-20261115.exe
exit /b 0
