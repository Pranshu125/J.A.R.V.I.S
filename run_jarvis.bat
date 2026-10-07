@echo off
title J.A.R.V.I.S.
cd /d "%~dp0"
call .\venv\Scripts\activate
start pythonw jarvis_ui.py
