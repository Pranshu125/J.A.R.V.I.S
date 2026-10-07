@echo off
title J.A.R.V.I.S. Core
echo ==============================================
echo [JARVIS] Initializing Mixed Reality Systems...
echo ==============================================
cd /d "%~dp0"

:: Start the local Ollama server silently in the background
echo [JARVIS] Waking up Neural Engine (Ollama)...
Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue

:: Activate the Python environment and launch the master script
call venv\Scripts\activate
python jarvis_master.py

pause
