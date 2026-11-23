import json
import re
import secrets
from datetime import datetime, timedelta
from urllib.request import Request,urlopen

HELP="""Shaxsiy zaxira
/zpair — telefonni ulash uchun 5 daqiqalik kod
/zaxira — oxirgi 10 ta hujjat
/zfind diplom — fayl nomidan qidirish
/zol_ID — tanlangan nusxani shu chatga yuborish
/zoff — telefondan yangi yuklashni yopish
Oddiy so‘rov: Diplomimni top"""

LAST_MONTH = re.compile(r"(?<!\w)o[‘’ʻʼ']tgan\s+oy(?:da)?(?:\s+saqlagan(?:im)?|\s+zaxiralagan(?:im)?)?(?!\w)", re.IGNORECASE)

def search_backups(vault, query):
    if not LAST_MONTH.search(query):
        return vault.search(query)
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month = (current_month - timedelta(days=1)).replace(day=1)
    return vault.search(
        LAST_MONTH.sub(" ", query),
        start=int(previous_month.timestamp()),
        end=int(current_month.timestamp()),
    )

def send_bytes(tg,name,data):
    boundary=secrets.token_hex(24)
    # Keep even unusual user-selected filenames within one multipart header.
    display=name.replace('"','_').replace('\\','_')
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{tg.owner}\r\n'
          f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{display}"\r\n'
          'Content-Type: application/octet-stream\r\n\r\n').encode()+data+f'\r\n--{boundary}--\r\n'.encode()
    req=Request('https://api.telegram.org/bot'+tg.token+'/sendDocument',data=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
    try:
        with urlopen(req,timeout=90) as response:
            if json.load(response).get('ok'):
                return
    except OSError:
        pass
    raise ValueError('Telegram faylni qabul qilmadi. Nusxa saqlangan. Olish buyrug‘ini qaytaring.')

class VaultCommands:
    def __init__(self,server,tg,deliver=None):
        self.server=server
        self.tg=tg
        self.deliver=deliver or (lambda n,b:send_bytes(tg,n,b))
    def handle(self,text):
        first,_,arg=text.strip().partition(' ')
        cmd=first.split('@')[0].casefold()
        if cmd=='/zhelp':
            self.tg.send(HELP)
        elif cmd=='/zregister':
            self.tg.send('Hisob ochish kodi (5 daqiqa): '+self.server.enroll.issue())
        elif cmd=='/zpair':
            self.tg.send('Telefondagi Zaxira ilovasiga kiriting. 5 daqiqa amal qiladi. Boshqalarga bermang.\n'+self.server.pairing.issue())
        elif cmd=='/zoff':
            self.server.pairing.revoke()
            self.tg.send('Telefondan yangi yuklash yopildi. Oldingi zaxiralar saqlangan.')
        elif re.fullmatch(r'/zol_[0-9a-f]{16}',cmd) or cmd=='/zol':
            ident=cmd[5:] if cmd.startswith('/zol_') else arg.strip()
            name,content=self.server.vault.get(ident)
            self.deliver(name,content)
        else:
            if cmd in ('/zaxira','/zfind','/zai'):
                query=arg.strip()
            else:
                if text.startswith('/'):
                    return False
                match=re.fullmatch(r'(.{1,140}?)\s+(?:top|topib ber)(?:ing)?[.!?]*',text.strip(),re.IGNORECASE)
                if not match:
                    return False
                query=match[1]
            if cmd=='/zai':
                from .semantic import search
                if not query:
                    self.tg.send("Masalan: /zai oliy ta’limni tugatganim haqidagi hujjat")
                    return True
                try:
                    rows=search(self.server.vault,query)
                except (OSError,ValueError,KeyError,ZeroDivisionError):
                    self.tg.send("Windows’da Ollama va bge-m3 modelini ishga tushiring")
                    return True
            else:
                rows=search_backups(self.server.vault, query)
            lines=[f'{name} • {size:,} bayt • {datetime.fromtimestamp(stamp):%d.%m %H:%M}\n/zol_{ident}' for ident,name,size,stamp in rows]
            self.tg.send('Saqlangan nusxalar (10 tagacha). Olish uchun pastdagi buyruqni bosing.\n\n'+'\n\n'.join(lines) if rows else 'Zaxirada mos fayl yo‘q. /zaxira bilan oxirgi nusxalarni ko‘ring yoki telefondan hujjatni zaxiralang.')
        return True
