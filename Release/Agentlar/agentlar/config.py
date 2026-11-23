import json
import re
from pathlib import Path

def validate_config(config, base):
    for key in ('telegram_token','gemini_api_key','model'):
        if not isinstance(config.get(key),str) or not config[key].strip(): raise ValueError(key+' kiritilmagan. 1_SOZLASH.bat ni oching.')
    owner=config.get('owner_id')
    if type(owner) is not int or owner<=0: raise ValueError('owner_id musbat Telegram raqami bo‘lishi kerak')
    if type(config.get('allow_commands',False)) is not bool: raise ValueError('allow_commands true yoki false bo‘lsin')
    for key in ('allow_local_build','keep_awake','phone_enabled'):
        if type(config.get(key,False)) is not bool: raise ValueError(key+' true yoki false bo‘lsin')
    interval=config.get('gemini_min_interval',15)
    if type(interval) not in (int,float) or not 5<=interval<=120: raise ValueError('gemini_min_interval 5–120 soniya bo‘lsin')
    steps=config.get('max_steps',24)
    if type(steps) is not int or not 1<=steps<=48: raise ValueError('max_steps 1–48 bo‘lsin')
    sources=config.get('sources',{})
    if not isinstance(sources,dict): raise ValueError('sources obyekt bo‘lsin')
    base=Path(base).resolve()
    for alias,raw in sources.items():
        if not re.fullmatch('[A-Za-z0-9_-]{1,40}',alias): raise ValueError('Manba nomida faqat harf, raqam, _ va - ishlating')
        if not isinstance(raw,str): raise ValueError('Manba yo‘li matn bo‘lsin')
        p=Path(raw).expanduser().resolve()
        if not p.is_dir() or p==Path(p.anchor) or p==Path.home().resolve() or base.is_relative_to(p) or p.is_relative_to(base):
            raise ValueError('Manba sifatida alohida hujjatlar papkasini tanlang; disk, profil yoki Agentlar papkasi emas')
        sources[alias]=str(p)
    folders=config.get('pc_folders',{})
    if not isinstance(folders,dict):raise ValueError('pc_folders obyekt bo‘lsin')
    for alias,raw in folders.items():
        if not re.fullmatch('[A-Za-z0-9_-]{1,40}',alias) or not isinstance(raw,str):raise ValueError('PC papka nomi/yo‘li yaroqsiz')
        p=Path(raw).expanduser().resolve()
        if not p.is_dir() or p==Path(p.anchor) or p==Path.home().resolve() or base.is_relative_to(p) or p.is_relative_to(base):raise ValueError('PC uchun alohida hujjat papkasini tanlang')
        folders[alias]=str(p)
    return config

def load_config(base):
    path=Path(base)/'config.json'
    if not path.exists(): raise ValueError('Avval 1_SOZLASH.bat orqali sozlang')
    return validate_config(json.loads(path.read_text(encoding='utf-8-sig')),base)
