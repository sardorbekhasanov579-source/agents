@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "config.json" (
  echo Avval bu fayllarni oldingi config.json turgan Agentlar papkasiga ko'chiring yoki 1_SOZLASH.bat ni oching.
  goto :end
)
if not exist ".zaxira_env\Scripts\python.exe" (
  where py >nul 2>nul
  if errorlevel 1 (
    python -m venv ".zaxira_env"
  ) else (
    py -3 -m venv ".zaxira_env"
  )
  if errorlevel 1 goto :end
)
".zaxira_env\Scripts\python.exe" -c "import cryptography,pypdf" >nul 2>nul
if errorlevel 1 (
  ".zaxira_env\Scripts\python.exe" -m pip install -r zaxira-requirements.txt
  if errorlevel 1 goto :end
)
set "AGENTLAR_BACKUP=1"
".zaxira_env\Scripts\python.exe" main.py
:end
pause
