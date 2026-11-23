import getpass
import os
import secrets
import sys
import time
from pathlib import Path
from agentlar.api import Gemini, Telegram
from agentlar.config import validate_config
from agentlar.core import atomic_json

BASE=Path(__file__).resolve().parent

def setup():
    print('\nAGENTLAR TELEGRAM V1 — SOZLASH\n')
    print('Python 3.11 yoki yangi versiya talab qilinadi. Kalitlarni chatga yubormang.')
    if (BASE/'config.json').exists():
        if input('Mavjud sozlamani almashtirasizmi? HA deb yozing: ').strip().upper()!='HA': return
    print('\n1. Telegramda https://t.me/BotFather ni oching, /newbot bilan yangi bot yarating.')
    token=getpass.getpass('Bot tokeni (yashirin): ').strip()
    tg=Telegram(token); identity=tg.call('getMe')
    print('Bot tekshirildi: @'+identity['username'])
    print('\n2. https://aistudio.google.com/apikey orqali Gemini API kalitini oling.')
    key=getpass.getpass('Gemini API kaliti (yashirin): ').strip()
    models=Gemini.models(key)
    choices=[m for m in models if 'gemini' in m and not any(x in m for x in ('image','tts','audio','live','robot','embedding'))]
    if not choices: choices=models
    if not choices: raise ValueError('Ushbu kalit uchun generateContent modellari topilmadi')
    print('\nKalitingizdagi mavjud modellar (ro‘yxat API dan olindi):')
    for i,m in enumerate(choices,1): print(f'{i:2}. {m}')
    print('Birinchi sinov uchun hisobingizda mavjud Flash modelini tanlashingiz mumkin.')
    chosen=int(input('Model raqami: ').strip())
    if not 1<=chosen<=len(choices): raise ValueError('Model raqami yaroqsiz')
    model=choices[chosen-1]
    print('Modelga kichik test so‘rovi yuborilmoqda (API kvotasi ishlatiladi)...')
    check=Gemini(key,model).ask('Return only a JSON object with key ok set to true.', 'Connection test')
    if not isinstance(check,dict) or check.get('ok') is not True: raise ValueError('Model JSON testi o‘tmadi; boshqa modelni sinang')
    print('Gemini ulanishi tekshirildi.')
    print('\n3. Telegram hisobingizni biriktirish.')
    code=secrets.token_hex(6)
    tg.call('deleteWebhook',{'drop_pending_updates':True})
    print('Shaxsiy botingizni oching: https://t.me/'+identity['username'])
    print('Unga quyidagi matnni yuboring: /pair '+code)
    print('Bu kodni boshqalarga bermang. 5 daqiqa kutaman...')
    offset=0; owner=None; deadline=time.monotonic()+300
    while time.monotonic()<deadline and owner is None:
        for u in tg.call('getUpdates',{'offset':offset,'timeout':20,'allowed_updates':['message']},timeout=35):
            offset=u['update_id']+1
            msg=u.get('message',{})
            if msg.get('text','').strip()=='/pair '+code and msg.get('chat',{}).get('type')=='private':
                who=msg.get('from',{})
                if who.get('id')!=msg['chat'].get('id'): continue
                print('Hisob: '+str(who.get('first_name',''))+' @'+str(who.get('username',''))+' ID='+str(who['id']))
                if input('Bu sizmi? HA deb tasdiqlang: ').strip().upper()=='HA': owner=who['id']; break
    if owner is None: raise ValueError('Biriktirish tugamadi. Sozlashni qayta boshlang.')
    sources={}
    print('\n4. Shaxsiy manba papkasi (ixtiyoriy).')
    print('Faqat o‘qish ruxsati. O‘qilgan matnlar Gemini API ga yuboriladi. Maxfiy kalitlar va parollarni bu papkaga qo‘ymang.')
    raw=input('Alohida hujjatlar papkasining to‘liq yo‘li; kerak bo‘lmasa Enter: ').strip().strip('"')
    if raw: sources['hujjatlar']=raw
    config={'telegram_token':token,'gemini_api_key':key,'model':model,'owner_id':owner,
            'sources':sources,'max_steps':24,'allow_commands':False}
    validate_config(config,BASE)
    atomic_json(BASE/'config.json',config)
    try: os.chmod(BASE/'config.json',0o600)
    except OSError: pass
    atomic_json(BASE/'state'/'telegram_offset.json',{'offset':offset})
    tg.owner=owner; tg.send('Hisob biriktirildi. Endi kompyuterda 2_ISHGA_TUSHIRISH.bat ni oching.')
    print('\nSOZLANDI. 2_ISHGA_TUSHIRISH.bat ni oching. Kalitlar faqat shu kompyuterdagi config.json da saqlandi.')

if __name__=='__main__':
    try:
        if sys.version_info<(3,11): raise ValueError('Python 3.11+ kerak')
        setup()
    except (Exception,KeyboardInterrupt) as e:
        # API clients sanitize remote errors; never print config or request objects.
        print('\nSozlash yakunlanmadi: '+str(e)); sys.exit(1)
