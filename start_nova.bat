@echo off
set "PROJECT=%~dp0"
start "Nova Desktop Pet" /min cmd /c "%PROJECT%desktop-pet\pet_watchdog.bat"
start "Nova Vision Bridge" /b pythonw "%PROJECT%voice-engine\vision_bridge.py"
start "Nova Voice Engine" /b pythonw "%PROJECT%voice-engine\voice_assistant.py"
