from .enroll import Enrollment, START
from .recovery import Restore, FORM
from urllib.parse import quote
import base64
import hashlib
import hmac
import json
import secrets
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .store import MAX_FILE

class Pairing:
    """One phone, one owner, write-only session. The owner revokes access with /zoff."""
    def __init__(self, vault):
        self.vault=vault
        self.lock=threading.RLock()
        self.pending=None
        with vault.connection() as db:
            db.execute(f'CREATE TABLE IF NOT EXISTS paired_phone (owner TEXT PRIMARY KEY, digest {vault.blob_type} NOT NULL)')
            row=db.execute('SELECT digest FROM paired_phone WHERE owner=?',(vault.owner,)).fetchone()
        self.device=row[0] if row else None
    def issue(self):
        with self.lock:
            code=secrets.token_urlsafe(18)
            self.pending=(hashlib.sha256(code.encode()).digest(),time.monotonic()+300)
            return code
    def exchange(self, code):
        with self.lock:
            if not isinstance(code,str) or not self.pending or time.monotonic()>self.pending[1] or not hmac.compare_digest(self.pending[0],hashlib.sha256(code.encode()).digest()):
                raise PermissionError()
            token=secrets.token_urlsafe(32)
            digest=hashlib.sha256(token.encode()).digest()
            with self.vault.connection() as db:
                db.execute('INSERT INTO paired_phone VALUES (?,?) ON CONFLICT(owner) DO UPDATE SET digest=excluded.digest',(self.vault.owner,digest))
            self.pending=None
            self.device=digest
            return token
    def require(self, header):
        if not header.startswith('Bearer '):
            raise PermissionError()
        with self.lock:
            if not self.device or not hmac.compare_digest(self.device,hashlib.sha256(header[7:].encode()).digest()):
                raise PermissionError()
    def revoke(self):
        with self.lock:
            with self.vault.connection() as db:
                db.execute('DELETE FROM paired_phone WHERE owner=?',(self.vault.owner,))
            self.pending=self.device=None

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,vault,port=8766,host="127.0.0.1"):
        self.enroll=Enrollment(vault)
        self.restore=Restore(vault)
        self.vault=vault
        self.pairing=Pairing(vault)
        self.slots=threading.BoundedSemaphore(6)
        super().__init__((host,port),Handler)
    def process_request(self,request,address):
        if not self.slots.acquire(False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request,address)
        except BaseException:
            self.slots.release()
            raise
    def process_request_thread(self,request,address):
        try:
            super().process_request_thread(request,address)
        finally:
            self.slots.release()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):
        pass
    def handle(self):
        self.connection.settimeout(15)
        def cut():
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        timer=threading.Timer(90,cut)
        timer.daemon=True
        timer.start()
        try:
            super().handle()
        finally:
            timer.cancel()
    def reply(self,code,body):
        raw=json.dumps(body,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(raw)
    def read_body(self,limit):
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length',[]))!=1:
            raise ValueError('Hajm ko‘rsatilishi kerak')
        length=int(self.headers['Content-Length'])
        if not 0<=length<=limit:
            raise ValueError('Ruxsat etilgan hajm oshdi')
        data=self.rfile.read(length)
        if len(data)!=length:
            raise ValueError('Yuklash uzildi')
        return data
    def page(self, data, content_type, filename=None):
        self.send_response(200)
        self.send_header('Content-Type',content_type)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'none'; form-action 'self'; frame-ancestors 'none'")
        if filename:
            self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(filename,safe=''))
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path=='/health':
            self.reply(200,{'ok': True})
        elif self.path=='/register':
            self.page(START.encode(),'text/html; charset=utf-8')
        elif self.path=='/restore':
            self.page(FORM.encode(),'text/html; charset=utf-8')
        else:
            self.reply(404,{'error':'Manzil topilmadi'})

    def do_POST(self):
        try:
            if self.path=='/telegram' and hasattr(self.server,'webhook'):
                self.server.webhook(self)
            elif self.path in ('/register/start','/register/finish'):
                action=self.server.enroll.start if self.path.endswith('/start') else self.server.enroll.finish
                self.page(action(self.read_body(4096)).encode(),'text/html; charset=utf-8')
            elif self.path=='/restore.json':
                self.page(self.server.restore.search(self.read_body(4096),as_json=True),'application/json')
            elif self.path=='/restore':
                html=self.server.restore.search(self.read_body(4096))
                self.page(html.encode(),'text/html; charset=utf-8')
            elif self.path=='/download':
                name,data=self.server.restore.download(self.read_body(512))
                self.page(data,'application/octet-stream',name)
            elif self.path=='/v1/pair':
                code=json.loads(self.read_body(512))['code']
                self.reply(200,{'token':self.server.pairing.exchange(code)})
            elif self.path=='/v1/documents':
                auth=self.headers.get('Authorization','')
                self.server.pairing.require(auth)
                name=base64.b64decode(self.headers.get('X-Name',''),validate=True).decode()
                payload=self.read_body(MAX_FILE)
                if self.headers.get('X-SHA256')!=hashlib.sha256(payload).hexdigest():
                    raise ValueError('Fayl tekshiruvdan o‘tmadi')
                with self.server.pairing.lock:
                    self.server.pairing.require(auth)
                    ident,created=self.server.vault.add(name,payload)
                from .cloud import mirror
                mirror(self.server.vault,ident,name,payload)
                self.reply(201 if created else 200,{'id':ident,'created':created})
            else:
                self.reply(404,{'error':'Manzil topilmadi'})
        except PermissionError:
            self.reply(403,{'error':'Ruxsat tugagan. /zpair bilan qayta ulang.'})
        except (ValueError,KeyError,TypeError):
            self.reply(400,{'error':'So‘rov, fayl nomi, tekshiruv yoki hajm xato. Bir fayl 10 MiB gacha. Ombor 512 MiB / 1000 nusxa.'})
        except (ConnectionError,TimeoutError):
            pass
        except Exception:
            self.reply(500,{'error':'Saqlash amalga oshmadi. Server diski va kalitni tekshiring.'})
