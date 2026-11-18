@echo off
REM DualCam Studio - ONE-TIME virtual camera driver setup. NO OBS needed.
REM Registers the free UnityCapture DirectShow driver (MIT licence,
REM github.com/schellingb/UnityCapture) so Zoom sees "Unity Video Capture".
REM Windows asks for admin (UAC) once - that is for the driver only.
REM DualCam Studio itself never needs admin after this.
title DualCam Studio - Virtual Camera Driver Setup (one time)

REM --- self-elevate to admin for regsvr32 ---
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Asking Windows for admin permission - click YES on the UAC prompt...
  powershell -Command "Start-Process '%~f0' -Verb RunAs"
  exit /b
)

set "DRV=%SystemDrive%\DualCamStudio\driver"
if not exist "%DRV%" mkdir "%DRV%"
cd /d "%DRV%"

if not exist "UnityCaptureFilter64.dll" (
  echo Downloading UnityCapture driver from GitHub...
  powershell -Command "Invoke-WebRequest -Uri 'https://github.com/schellingb/UnityCapture/archive/refs/heads/master.zip' -OutFile 'uc.zip'"
  if not exist "uc.zip" (
    echo Download FAILED. Check internet, then open this page and download the ZIP manually:
    echo https://github.com/schellingb/UnityCapture
    pause
    exit /b 1
  )
  powershell -Command "Expand-Archive -Force 'uc.zip' '.'"
  copy /y "UnityCapture-master\Install\UnityCaptureFilter32.dll" "." >nul
  copy /y "UnityCapture-master\Install\UnityCaptureFilter64.dll" "." >nul
)

echo Registering virtual camera device...
regsvr32 /s "UnityCaptureFilter64.dll"
regsvr32 /s "UnityCaptureFilter32.dll"

echo.
echo DONE. A camera named "Unity Video Capture" is now in Windows.
echo 1. Open DualCam Studio, START STUDIO, then GO LIVE TO ZOOM.
echo 2. In the Zoom app: Settings - Video - Camera - Unity Video Capture.
echo 3. In the Zoom app: Settings - Audio - Microphone - your microphone.
echo Keep the files in %DRV% - deleting them removes the camera.
echo To uninstall later: run this file's folder copy of Uninstall info in README.
pause
