@echo off
set "ROOT=%~dp0"
:restart
pythonw "%ROOT%desktop_pet.py"
timeout /t 2 /nobreak >nul
goto restart
