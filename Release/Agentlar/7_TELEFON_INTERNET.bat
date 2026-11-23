@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 phone_tunnel.py
pause
