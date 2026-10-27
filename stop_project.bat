@echo off
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'ai_anomaly_detector|replay_real_data|streamlit' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Smart meter project stopped.
pause