@echo off
set "PROJECT=%~dp0"
start "Nova Desktop Pet" /min pythonw "%PROJECT%desktop-pet\desktop_pet.py"
start "Nova Voice Engine" cmd /k "cd /d "%PROJECT%voice-engine" && python voice_assistant.py"
