@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    python zaxira_tunnel.py
) else (
    py -3 zaxira_tunnel.py
)
pause
