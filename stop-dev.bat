@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "DEVCTL=%SCRIPT_DIR%devctl.py"
set "EXIT_CODE=0"

if not exist "%DEVCTL%" (
  echo [ERROR] devctl.py was not found: "%DEVCTL%"
  set "EXIT_CODE=1"
  goto :end
)

py -3 --version >nul 2>nul
if %errorlevel%==0 (
  echo [RUN] py -3 "%DEVCTL%" down
  py -3 "%DEVCTL%" down
  set "EXIT_CODE=%errorlevel%"
  goto :end
)

python --version >nul 2>nul
if %errorlevel%==0 (
  echo [RUN] python "%DEVCTL%" down
  python "%DEVCTL%" down
  set "EXIT_CODE=%errorlevel%"
  goto :end
)

echo [ERROR] Python 3 is not installed. Install Python 3 and run again.
set "EXIT_CODE=1"

:end
if not "%NO_PAUSE%"=="1" pause
exit /b %EXIT_CODE%
