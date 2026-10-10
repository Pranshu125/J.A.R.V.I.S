@echo off
title J.A.R.V.I.S. Core
color 0B
echo [JARVIS] Booting J.A.R.V.I.S. Cognitive OS...
cd /d "D:\JARVIS"
start /B ollama serve >nul 2>&1
call venv\Scripts\activate
python jarvis_master.py
exit

