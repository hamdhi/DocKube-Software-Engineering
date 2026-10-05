@echo off
setlocal

REM DocKube launcher: double-click this file.
REM Prefer the packaged EXE if it has been built, otherwise run from source.

cd /d "%~dp0"

set "EXE=%~dp0dist\DocKube.exe"
if exist "%EXE%" (
    echo Starting DocKube from the packaged executable...
    start "" "%EXE%"
    goto :eof
)

echo Starting DocKube with Python...
where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw "%~dp0app.py"
    goto :eof
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0app.py"
    goto :eof
)

echo.
echo ERROR: Python was not found on this machine.
echo Install Python 3.10 or newer from https://www.python.org/downloads/
echo and make sure "Add Python to PATH" is selected during setup.
echo.
pause
endlocal