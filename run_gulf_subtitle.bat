@echo off
setlocal EnableExtensions
title GULF Subtitle + Text V2

echo ============================================================
echo GULF Subtitle + Text V2
echo Local-first subtitle processing / Review before final
echo ============================================================
echo.

set "ROOT=%~dp0"
set "VENV=%ROOT%.gulf_venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%ROOT%backend\app\main.py" (
  echo [ERROR] backend\app\main.py was not found.
  pause
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found in PATH.
  echo Install Python 3.11+ and enable the Python launcher/PATH.
  pause
  exit /b 1
)

if not exist "%PY%" (
  echo [1/4] Creating private environment...
  python -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] Could not create the private environment.
    pause
    exit /b 1
  )
)

echo [2/4] Updating pip...
"%PY%" -m pip install --upgrade pip --disable-pip-version-check -q
if errorlevel 1 (
  echo [ERROR] pip update failed.
  pause
  exit /b 1
)

echo [3/4] Checking local processing packages...
"%PY%" -c "import fastapi,uvicorn,faster_whisper; import imageio_ffmpeg; import transformers,torch; print('CORE_PACKAGES_PASS')" >nul 2>&1
if errorlevel 1 (
  echo Installing the first-run packages. This can be large.
  "%PY%" -m pip install -r "%ROOT%backend\requirements-gulf-v2.txt" --disable-pip-version-check
  if errorlevel 1 (
    echo.
    echo [ERROR] Package installation failed.
    echo The original repository was not changed.
    pause
    exit /b 1
  )
)

echo [4/4] Starting GULF Subtitle + Text V2...
cd /d "%ROOT%"
start "GULF Subtitle V2 Server" cmd /k ""%PY%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8765/ui/"

echo.
echo ============================================================
echo Browser: http://127.0.0.1:8765/ui/
echo Close the GULF Subtitle V2 Server window to stop the service.
echo ============================================================
echo.
exit /b 0
