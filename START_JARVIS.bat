@echo off
title J.A.R.V.I.S. Core
color 0B
echo ========================================================
echo        J.A.R.V.I.S. COGNITIVE OPERATING SYSTEM
echo ========================================================
echo [JARVIS] Initializing workspace...
cd /d "%~dp0"

if exist ".env" (
    for /f "tokens=1,2 delims==" %%A in (.env) do (
        if "%%A"=="GEMINI_API_KEY" set GEMINI_API_KEY=%%B
    )
)

if defined GEMINI_API_KEY (
    echo [JARVIS] Cloud Acceleration: Active (Google Gemini 3.8 Flash)
) else (
    echo [JARVIS] Local Autonomous Mode: Active (Ollama)
)

start /B ollama serve >nul 2>&1

echo [JARVIS] Launching 3D Holographic Interface...
"%~dp0venv\Scripts\python.exe" jarvis_master.py

if %ERRORLEVEL% NEQ 0 (
    echo [JARVIS] Process terminated with code %ERRORLEVEL%.
    pause
)
exit
