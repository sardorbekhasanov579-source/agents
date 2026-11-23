"""Authenticated bounded phone queue; bind loopback, expose only via HTTPS tunnel."""
import base64,hashlib,hmac,json,re,secrets,threading,time,socket
from socketserver import ThreadingMixIn
from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from .devices import LIMIT
class PhoneBridge:
 def __init__(self,base,notify,deliver):
  self.base=Path(base);self.notify=notify;self.deliver=deliver;self.lock=threading.RLock()
  self.code=None;self.code_until=0;self.token_hash=None;self.queue=[];self.completed=[];self.last_seen=0;self.info={};self.server=None;self.attempts=[]
 def new_pair(self):
  with self.lock:
   self.code=secrets.token_hex(12);self.code_until=time.time()+300;return self.code
 def pair(self,code):
  with self.lock:
   now=time.time();self.attempts=[x for x in self.attempts if now-x<60]
   if len(self.attempts)>=10:raise ValueError('Kutib qayta urining')
   self.attempts.append(now)
   if not isinstance(code,str) or not self.code or now>self.code_until or not hmac.compare_digest(code,self.code):raise ValueError('Kod yaroqsiz')
   self.revoke();token=secrets.token_urlsafe(32);self.token_hash=hashlib.sha256(token.encode()).digest();return token
 def auth(self,token):
  if not isinstance(token,str) or not self.token_hash or not hmac.compare_digest(hashlib.sha256(token.encode()).digest(),self.token_hash):raise ValueError('Ulanish bekor qilingan; qayta ulang')
 def revoke(self):
  with self.lock:
   self.token_hash=None;self.code=None;self.queue=[];self.completed=[];self.last_seen=0;self.info={}
 def enqueue(self,action,**args):
  if action not in ('search','get','put'):raise ValueError('Amal yaroqsiz')
  with self.lock:
   if not self.token_hash:raise ValueError('Avval telefonni /phonepair bilan ulang')
   self.queue=[q for q in self.queue if q['expires']>time.time()]
   if len(self.queue)>=10:raise ValueError('Telefon navbati to‘la')
   ident=secrets.token_hex(12);self.queue.append({'id':ident,'action':action,'expires':time.time()+300,**args});return ident
 def poll(self,token,info):
  with self.lock:
   self.auth(token);self.last_seen=time.time()
   self.info={k:str(info.get(k,''))[:200] for k in ('battery','folder','receive','device')}
   self.queue=[q for q in self.queue if q['expires']>time.time()]
   return {'command':self.queue[0] if self.queue else None}
 def result(self,token,ident,value):
  with self.lock:
   self.auth(token)
   if ident in self.completed:return # retry of acknowledged result
   if not self.queue or self.queue[0]['id']!=ident:raise ValueError('Buyruq topilmadi')
   action=self.queue[0]['action'];path=None
   if not isinstance(value,dict):raise ValueError('Natija formati')
   if 'data' in value:
    if action!='get':raise ValueError('Kutilmagan fayl')
    data=base64.b64decode(value['data'],validate=True)
    if len(data)>LIMIT:raise ValueError('4 MiB limit')
    name=str(value.get('name','phone-file'));name=re.sub(r'[^\w. -]','_',name)[:100].strip(' .') or 'phone-file'
    out=self.base/'phone_received';out.mkdir(parents=True,exist_ok=True);path=out/(ident+'_'+name);path.write_bytes(data)
   text=str(value.get('text','Tayyor'))[:6000]
   self.queue.pop(0);self.completed=(self.completed+[ident])[-100:]
  # Delivery outside lock, asynchronously so Telegram network cannot block phone polling.
  def send():
   try:
    self.notify('Telefon: '+text)
    if path:self.deliver(path)
   except Exception:print('Telefon natijasi Telegramga yuborilmadi; phone_received papkasini tekshiring.')
  threading.Thread(target=send,daemon=True).start()
 def status(self):
  with self.lock:
   age=int(time.time()-self.last_seen) if self.last_seen else None
   return ('Ulanish: '+('biriktirilgan' if self.token_hash else 'yo‘q')+'\nOxirgi aloqa: '+(str(age)+' soniya oldin' if age is not None else 'hali yo‘q')+'\nBatareya: '+self.info.get('battery','—')+'%\nPapka: '+self.info.get('folder','—')+'\nQabul qilish: '+self.info.get('receive','—')+'\nNavbat: '+str(len(self.queue)))
 def start(self,port=8765):
  bridge=self
  class Handler(BaseHTTPRequestHandler):
   def handle(self):
    def timeout():
     try:self.connection.shutdown(socket.SHUT_RDWR)
     except OSError:pass
    timer=threading.Timer(15,timeout);timer.daemon=True;timer.start()
    try:super().handle()
    finally:timer.cancel()
   def log_message(self,*args):pass # never log credentials or personal paths
   def setup(self):
    super().setup();self.connection.settimeout(15)
   def do_POST(self):
    try:
     n=int(self.headers.get('Content-Length','0'))
     if n<2 or n>6*1024*1024:raise ValueError('Hajm limiti')
     if self.headers.get('Transfer-Encoding'):raise ValueError('Transfer encoding yo‘q')
     if self.path not in ('/pair','/poll','/result'):raise ValueError('Endpoint yo‘q')
     token=self.headers.get('Authorization','').removeprefix('Bearer ')
     if self.path!='/pair':
      with bridge.lock:bridge.auth(token)
     elif n>1024:raise ValueError('Hajm limiti')
     body=json.loads(self.rfile.read(n))
     if not isinstance(body,dict):raise ValueError('JSON obyekt kerak')
     if self.path=='/pair':result={'token':bridge.pair(body.get('code'))}
     elif self.path=='/poll':result=bridge.poll(token,body)
     else:bridge.result(token,body.get('id'),body.get('result'));result={'ok':True}
     self.respond(200,result)
    except Exception:
     self.respond(400,{'error':'So‘rov rad etildi. Ulanish, kod yoki hajmni tekshiring.'})
   def respond(self,status,data):
    raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers()
    try:self.wfile.write(raw)
    except OSError:pass
  class BoundedServer(ThreadingMixIn,HTTPServer):
   daemon_threads=True
   def __init__(self,*args):self.slots=threading.BoundedSemaphore(8);super().__init__(*args)
   def process_request(self,request,address):
    if not self.slots.acquire(blocking=False):self.shutdown_request(request);return
    try:super().process_request(request,address)
    except Exception:self.slots.release();raise
   def process_request_thread(self,request,address):
    try:super().process_request_thread(request,address)
    finally:self.slots.release()
  self.server=BoundedServer(('127.0.0.1',port),Handler)
  threading.Thread(target=self.server.serve_forever,daemon=True).start()
 def close(self):
  self.revoke()
  if self.server:self.server.shutdown();self.server.server_close()
