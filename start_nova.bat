@echo off
set "PROJECT=%~dp0"
where ollama >nul 2>&1
if errorlevel 1 goto skip_ollama
curl --silent --fail http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 start "Nova Ollama" /min cmd /c "ollama serve"
:skip_ollama
start "Nova Desktop Pet" /min cmd /c "%PROJECT%desktop-pet\pet_watchdog.bat"
start "Nova Vision Bridge" /b pythonw "%PROJECT%voice-engine\vision_bridge.py"
start "Nova Voice Engine" /b pythonw "%PROJECT%voice-engine\voice_assistant.py"
