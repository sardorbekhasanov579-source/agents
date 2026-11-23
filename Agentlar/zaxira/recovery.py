"""Single-owner recovery portal, provisioned locally on the owner's Windows PC."""
import os
import base64
import getpass
import hashlib
import hmac
import json
import re
import secrets
import time
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs
from html import escape

FORM = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Zaxirani tiklash</title><h1>Zaxirani tiklash</h1><form method=post action="/restore"><p><label>Telefon raqami <input type=tel name=phone required></label><p><label>Parol <input type=password name=password required></label><p><label>Tiklash kodi <input type=password name=code required></label><p><label>Fayl nomi yoki so‘z <input name=query></label><p><button>Izlash</button></form>"""

def verifier(phone, password, code, salt):
    payload = json.dumps([phone.strip(), password, code.strip()], ensure_ascii=False).encode()
    return hashlib.scrypt(payload, salt=salt, n=2**15, r=8, p=1, maxmem=64*1024*1024).hex()

def provision():
    path = Path(os.environ.get('ZAXIRA_DATA_DIR', Path(__file__).resolve().parents[1] / 'private_backup')) / 'recovery.json'
    if path.exists():
        raise ValueError('Tiklash hisobi allaqachon sozlangan')
    phone = input('Telefon raqami (+998...): ').strip()
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', phone):
        raise ValueError('Xalqaro raqamni kiriting')
    email=input('Tasdiqlanadigan Gmail manzili: ').strip().lower()
    if not re.fullmatch(r'[a-z0-9._+%-]+@gmail\.com',email):
        raise ValueError('Gmail manzili xato')
    from .verify import verify_owner
    verify_owner(phone,email)
    password = getpass.getpass('Yangi parol (kamida 12 belgi): ')
    if len(password)<12 or password!=getpass.getpass('Parolni takrorlang: '):
        raise ValueError('Parol uzunligi yoki takrorlanishi xato')
    salt=secrets.token_bytes(16)
    code=secrets.token_urlsafe(24)
    record={'salt':salt.hex(), 'hash':verifier(phone,password,code,salt)}
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as stream:
        json.dump(record,stream)
    print('Tiklash kodini telefondan tashqarida saqlang:',code)

class Restore:
    def __init__(self,vault):
        self.vault=vault
        self.lock=Lock()
        self.attempts=[]
        self.downloads={}

    def search(self,raw,as_json=False):
        fields=parse_qs(raw.decode(), max_num_fields=4)
        with self.lock:
            now=time.monotonic()
            self.attempts=[t for t in self.attempts if t>now-300]
            if len(self.attempts)>=8: raise PermissionError()
            record=self.vault.recovery_record()
            if record is None: raise PermissionError()
            self.attempts.append(now)
            actual=verifier(fields['phone'][0],fields['password'][0],fields['code'][0],bytes.fromhex(record['salt']))
            if not hmac.compare_digest(actual,record['hash']): raise PermissionError()
            self.attempts.clear()
            self.downloads={key:value for key,value in self.downloads.items() if value[0]>now}
            from .bot import search_backups
            query = re.sub(r'\s+top(?:ib ber)?[.!?]*$', '', fields.get('query',[''])[0].strip(), flags=re.I)
            rows=search_backups(self.vault,query)
            links=[]
            items=[]
            for ident,name,size,stamp in rows:
                ticket=secrets.token_urlsafe(24)
                self.downloads[ticket]=(now+180,ident)
                item={"name":name,"ticket":ticket,"stamp":stamp,"size":size}
                if as_json and name=="Joylashuv.txt" and size<4096:
                    lines=self.vault.get(ident)[1].decode('utf8',errors='replace').splitlines()
                    if len(lines)>=3 and re.fullmatch(r'https://www\.google\.com/maps\?q=-?[0-9.]+,-?[0-9.]+',lines[-1]):
                        item.update(map_url=lines[-1],address=lines[-2],measured=lines[0])
                items.append(item)
                links.append(f'<p><form method=post action="/download"><input type=hidden name=ticket value="{ticket}"><button>{escape(name)} ({size} bayt)</button></form>')
            if as_json: return json.dumps(items).encode()
            return '<meta charset=utf-8><h1>Topilgan nusxalar</h1>'+(''.join(links) or '<p>Mos fayl topilmadi')+'<p><a href="/restore">Qayta izlash</a>'

    def download(self,raw):
        ticket=parse_qs(raw.decode(),max_num_fields=1)['ticket'][0]
        with self.lock:
            entry=self.downloads.pop(ticket,None)
            if not entry or entry[0]<time.monotonic(): raise PermissionError()
        return self.vault.get(entry[1])

if __name__=='__main__':
    provision()
