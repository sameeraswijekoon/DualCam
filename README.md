# DualCam Studio - 2 Cameras + Mic for Zoom (replaces OBS)

## WEB VIEW (no admin, no install) - LIVE
Open in Chrome / Edge: https://sameeraswijekoon.github.io/DualCam/

Teach - web view steps:
1. Plug in both cameras. Close Zoom/Teams (they lock cameras).
2. Open the live link above in Chrome. Click "1. Detect Devices" - Allow camera + microphone.
3. Pick Camera 1, Camera 2 and Microphone on the right panel.
4. Click "2. START STUDIO" - Program shows both cameras, mic meter moves.
5. Choose a Scene on the left (Side by Side / Picture in Picture / Top-Bottom / Solo).
6. Use it in the Zoom APP (installed Zoom Workplace):
   - No-admin way: Zoom meeting - Share Screen - select the Chrome window
     (click "Program Only (Clean)" in Studio first) - Share.
   - Camera-input way needs a virtual camera driver registered ONCE with
     admin (see desktop version below). On a work PC without admin this
     step is blocked by Windows itself - for every app, not just this one.

## DESKTOP APP (own virtual camera, NO OBS) - folder: desktop/
- studio_app.py - DualCam Studio EXE source (scenes, mic meter, GO LIVE
  to its own "Unity Video Capture" virtual camera).
- Setup_Virtual_Camera.bat - one-time driver setup (needs admin ONCE).
- BUILD_EXE_ON_THIS_PC.bat - builds DualCamStudio.exe with no admin
  (needs a user install of Python).
- In Zoom app: Settings - Video - Camera - "Unity Video Capture",
  Settings - Audio - Microphone - your microphone.

## Why GitHub?
The web view is hosted free on GitHub Pages, so a work PC with no admin
can run it from a link - nothing to install. The EXE build on GitHub
Actions is currently blocked by a billing lock on the account
("account is locked due to a billing issue") - fix it at
github.com - Settings - Billing, or build the EXE locally with the bat.
