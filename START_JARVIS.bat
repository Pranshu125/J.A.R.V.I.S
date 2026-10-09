@echo off
title J.A.R.V.I.S. Core
color 0B
echo [JARVIS] Booting The Ultimate Mark-XXXIX Clone...
cd /d "D:\JARVIS"
start /B ollama serve >nul 2>&1
call venv\Scripts\activate
python jarvis_master.py
exit
