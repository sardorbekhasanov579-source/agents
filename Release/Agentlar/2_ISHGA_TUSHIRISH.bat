@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 main.py
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python topilmadi. python.org dan Python 3.11+ o'rnating.
        echo Add python.exe to PATH ni belgilang.
    ) else (
        python main.py
    )
)
pause
