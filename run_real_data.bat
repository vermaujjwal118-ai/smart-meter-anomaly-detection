@echo off
title Smart Meter - Real Data Launcher
cd /d "%~dp0"

start "Dashboard" cmd /k python -m streamlit run dashboard_streamlit.py
timeout /t 15 /nobreak >nul
start "Replay (real data)" cmd /k python -u replay_real_data.py