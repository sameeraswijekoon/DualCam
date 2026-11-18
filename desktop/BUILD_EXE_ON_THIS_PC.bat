@echo off
REM Build DualCamStudio.exe ON THIS PC - no GitHub, no admin.
REM Needs Python (user install from python.org, tick "Add Python to PATH").
title Building DualCamStudio.exe
echo [1/3] Installing build tools to your user folder...
python -m pip install --user --upgrade opencv-python numpy Pillow pyvirtualcam sounddevice pyinstaller
if errorlevel 1 (
  echo Python not found. Install Python from python.org as a normal user install, tick "Add Python to PATH", then run this file again.
  pause
  exit /b 1
)
echo [2/3] Building DualCamStudio.exe ...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name DualCamStudio studio_app.py
echo [3/3] Done - your EXE is in the dist folder:
echo %CD%\dist\DualCamStudio.exe
echo Copy Setup_Virtual_Camera.bat next to it and run that bat ONCE.
pause
