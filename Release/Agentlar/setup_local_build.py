"""Enable local execution on the owner's computer without replacing API keys."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from agentlar.config import load_config
from agentlar.core import atomic_json

BASE=Path(__file__).resolve().parent

def main():
    print('AGENTLAR V1.2 — KOMPYUTERDA DASTUR YIG‘ISH\n')
    print('Avval bot oynasini Ctrl+C bilan to‘xtating.')
    config=load_config(BASE)
    print('Python:',sys.version.split()[0],sys.executable)
    for name in ('node','npm','git','wsl'):
        path=shutil.which(name)
        print(name+': '+(path or 'TOPILMADI'))
    if not shutil.which('node') or not shutil.which('npm'):
        print('\nWeb build uchun Node.js LTS kerak: https://nodejs.org/en/download')
        print('Node o‘rnatilgach bu oynani qayta oching. Python/static loyihalar ishlashi mumkin.')
    print('\nBu versiya Windowsda ishlaydi; WSL ichiga avtomatik dastur o‘rnatmaydi.')
    print('Gemini bulutda ishlaydi. RTX 5070 bu API uchun majburiy emas.')
    print('\nLOCAL BUILD RUXSATI: agent yozgan kod, npm/pip kutubxonalari, test va build skriptlari')
    print('sizning Windows hisobingiz huquqida avtomatik ishlaydi. Bu sandbox EMAS.')
    print('Ular loyiha papkasidan tashqaridagi fayllar va internetga ham kira oladi.')
    print('Faqat o‘zingiz bergan topshiriqlarni ishlating. Boshqa odamlarning noma’lum kodini yubormang.')
    print('Alohida Windows foydalanuvchisi yoki virtual mashina xavfni kamaytiradi.')
    print('Umumiy erkin shell buyruqlari o‘z-o‘zidan yoqilmaydi; faqat web/python/static build profillari.')
    answer=input('\nLocal buildni yoqish uchun HA, o‘chirish uchun YOQ: ').strip().upper()
    if answer not in ('HA','YOQ'): print('Hech narsa o‘zgarmadi.'); return
    config['allow_local_build']=answer=='HA'
    config['keep_awake']=answer=='HA'
    config.setdefault('gemini_min_interval',15)
    backup=BASE/'config.before-local-build.json'
    if not backup.exists(): shutil.copy2(BASE/'config.json',backup)
    atomic_json(BASE/'config.json',config)
    print('\nSaqlandi. API kalitlari va model saqlandi. Botni 2_ISHGA_TUSHIRISH.bat bilan oching.')
    print('Kalitlar bor config*.json fayllarini hech kimga yubormang.')

if __name__=='__main__':
    try: main()
    except Exception as exc: print('Sozlash tugamadi: '+str(exc)); sys.exit(1)
