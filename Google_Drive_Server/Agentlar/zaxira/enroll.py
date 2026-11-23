"""One-owner enrollment authorized by a short-lived private Telegram code."""
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from urllib.parse import parse_qs
from .recovery import verifier
from .verify import provider

START = """<meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><h1>Tiklash hisobini ochish</h1><form method=post action=/register/start><p>Botga /zregister yuboring.</p><label>Telegram kodi <input type=password name=grant required></label><p><label>Raqam (+998…) <input name=phone type=tel required></label><p><label>Gmail <input name=email type=email required></label><p><button>Kodlarni yuborish</button></form>"""

class Enrollment:
    def __init__(self, vault, send=provider):
        self.vault=vault
        self.lock=threading.Lock()
        self.grant=None
        self.challenge=None
        self.send=send

    def issue(self):
        with self.lock:
            if self.vault.recovery_record() is not None: raise ValueError('Hisob oldin ochilgan')
            raw=secrets.token_urlsafe(18)
            self.grant=(hashlib.sha256(raw.encode()).digest(),time.monotonic()+300)
            return raw

    def start(self,raw):
        data=parse_qs(raw.decode(),max_num_fields=3)
        phone=data['phone'][0].strip()
        email=data['email'][0].strip().lower()
        if not re.fullmatch(r'\+[1-9]\d{7,14}',phone) or not re.fullmatch(r'[a-z0-9._+%-]+@gmail\.com',email):
            raise ValueError('Telefon yoki Gmail xato')
        with self.lock:
            if self.vault.recovery_record() is not None or not self.grant or self.grant[1]<time.monotonic() or not hmac.compare_digest(
                    self.grant[0],hashlib.sha256(data['grant'][0].strip().encode()).digest()):
                raise PermissionError()
            self.grant=None
            self.challenge=None
            self.send('Verifications',{'Channel':'sms','To':phone})
            self.send('Verifications',{'Channel':'email','To':email})
            nonce=secrets.token_urlsafe(24)
            self.challenge=(nonce,phone,email,time.monotonic()+300)
            return f'<meta charset=utf-8><h1>Kodlarni tasdiqlash</h1><form method=post action=/register/finish><input type=hidden name=nonce value="{nonce}"><p>SMS kodi <input name=sms required><p>Gmail kodi <input name=emailcode required><p>Parol (kamida 12 belgi) <input type=password name=password minlength=12 required><p><button>Hisob ochish</button></form>'

    def finish(self,raw):
        data=parse_qs(raw.decode(),max_num_fields=4)
        with self.lock:
            if self.vault.recovery_record() is not None or not self.challenge: raise PermissionError()
            nonce,phone,email,deadline=self.challenge
            if deadline<time.monotonic() or not hmac.compare_digest(nonce,data['nonce'][0]): raise PermissionError()
            password=data['password'][0]
            if len(password)<12: raise ValueError('Parol qisqa')
            self.challenge=None
            for target,field in [(phone,'sms'),(email,'emailcode')]:
                if self.send('VerificationCheck',{'To':target,'Code':data[field][0]}).get('status')!='approved':
                    raise PermissionError()
            salt=secrets.token_bytes(16)
            code=secrets.token_urlsafe(24)
            record={'salt':salt.hex(),'hash':verifier(phone,password,code,salt)}
            self.vault.create_recovery(record)
            return '<meta charset=utf-8><h1>Hisob ochildi</h1><p>Tiklash kodini telefondan alohida saqlang.</p><code>'+code+'</code>'
