DualCam Studio - OBS replacement for Zoom
==========================================

ONE-TIME SETUP (2 minutes)
1. Double-click Setup_Virtual_Camera.bat - click YES on the Windows
   admin prompt. It registers the free UnityCapture virtual camera
   driver (no OBS). You only do this once.
2. That's it.

EVERY DAY USE
1. Open DualCamStudio.exe
2. START STUDIO - check both cameras and the mic meter move.
3. GO LIVE TO ZOOM - status shows "Streaming to: Unity Video Capture".
4. Open the Zoom app (Zoom Workplace):
   Settings - Video - Camera - "Unity Video Capture"
   Settings - Audio - Microphone - your microphone
5. Join your meeting. Your Zoom video is the Studio output - both
   cameras, your chosen scene - like a normal camera input.

Scenes: Side by Side, Picture in Picture, Top / Bottom, Cam 1 Solo,
Cam 2 Solo. Swap, mirror and labels are on the right panel.

Note on audio: a virtual camera carries video only - OBS works the
same way. Your voice goes through the microphone you select in Zoom.

Uninstall the driver: open an admin Command Prompt in
C:\DualCamStudio\driver and run:
  regsvr32 /u UnityCaptureFilter64.dll
  regsvr32 /u UnityCaptureFilter32.dll
then delete the C:\DualCamStudio folder.
