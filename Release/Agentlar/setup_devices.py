import json,sys,re
from pathlib import Path
from agentlar.core import atomic_json
from agentlar.config import validate_config
BASE=Path(__file__).resolve().parent
try:
 p=BASE/'config.json';c=json.loads(p.read_text(encoding='utf-8-sig'))
 if '--phone' in sys.argv:
  c['phone_enabled']=True
  print('Telefon moduli yoqildi. Botni qayta oching. 7_TELEFON_INTERNET.bat tunnelni ochadi.')
 else:
  from tkinter import Tk,filedialog
  print('Telegram orqali qidirish, yuklab olish va tasdiqlangan matn tahriri uchun bitta hujjat papkasini tanlang.')
  ui=Tk();ui.withdraw();folder=filedialog.askdirectory(title='Agentlar kira oladigan hujjatlar papkasi');ui.destroy()
  if not folder:raise ValueError('Papka tanlanmadi')
  alias=input('Papka qisqa nomi (masalan hujjat): ').strip()
  if not re.fullmatch('[A-Za-z0-9_-]{1,40}',alias):raise ValueError('Faqat lotin harfi, raqam, _ va -')
  c.setdefault('pc_folders',{})[alias]=folder
 validate_config(c,BASE);atomic_json(p,c)
 print('Saqlandi. 2_ISHGA_TUSHIRISH.bat orqali botni qayta oching. Telegram: /devices')
except Exception as e:print('Sozlanmadi: '+str(e));sys.exit(1)
