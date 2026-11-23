@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist config.json (
    where py >nul 2>nul
    if errorlevel 1 (
        python setup_agent.py
    ) else (
        py -3 setup_agent.py
    )
    if errorlevel 1 goto fail
)
if not exist config.json goto fail
where cloudflared >nul 2>nul
if errorlevel 1 (
    echo Internet tunneli uchun cloudflared kerak. Qo'llanmani o'qing.
) else (
    start "Zaxira HTTPS" cmd /k call "%~dp09_ZAXIRA_INTERNET.bat"
)
call "%~dp08_ZAXIRA_START.bat"
exit /b
:fail
echo Sozlash yakunlanmadi. Python 3.11+ o'rnatilganini tekshiring.
pause
exit /b 1
