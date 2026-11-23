import shutil,subprocess,os
from pathlib import Path
exe=shutil.which('cloudflared')
if not exe:
 for root in (os.environ.get('ProgramFiles','C:/Program Files'),os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)')):
  p=Path(root)/'cloudflared'/'cloudflared.exe'
  if p.is_file():exe=str(p);break
if not exe:
 print('Cloudflared kerak. PowerShell da quyidagini bajaring, keyin bu oynani qayta oching:')
 print('winget install --id Cloudflare.cloudflared -e')
 raise SystemExit(1)
print('Bot ham ishlayotgan bo‘lsin. Pastdagi https://....trycloudflare.com manzilini telefon ilovasiga kiriting.')
print('Telegram: /phonepair. Bu oyna ochiq tursin. Har qayta ochishda manzil o‘zgaradi.')
try:subprocess.run([exe,'tunnel','--url','http://127.0.0.1:8765','--no-autoupdate'],check=False)
except KeyboardInterrupt:pass
