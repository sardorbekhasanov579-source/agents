"""Owner-directed, scoped local files. Never passed automatically to the LLM."""
import hashlib,os,secrets,time
from pathlib import Path
from .core import safe_path,GENERATED,is_binary
LIMIT=4*1024*1024
class PCFiles:
 def __init__(self,roots,state):
  self.roots=roots;self.state=Path(state);self.pending={}
 def path(self,name):
  alias,sep,rel=name.replace('\\','/').partition('/')
  if not sep or alias not in self.roots:raise ValueError('Yo‘l: papka_nomi/fayl.txt; /pcroots ni ko‘ring')
  return safe_path(self.roots[alias],rel)
 def find(self,query):
  rows=[];count=0
  for alias,root in self.roots.items():
   root=Path(root).resolve()
   for base,dirs,files in os.walk(root,followlinks=False):
    count+=len(dirs)
    if count>10000:return rows+['[Qidiruv limiti: 10000 yozuv]']
    allowed=[]
    for d in dirs:
     child=Path(base)/d
     try:
      reparse=bool(getattr(child.lstat(),'st_file_attributes',0)&0x400)
      if not d.startswith('.') and d not in GENERATED and not child.is_symlink() and not reparse and child.resolve().is_relative_to(root) and len(Path(base).relative_to(root).parts)<12:allowed.append(d)
     except OSError:pass
    dirs[:]=allowed
    for f in files:
     count+=1
     if count>10000:return rows+['[Qidiruv limiti: 10000 fayl]']
     if query.casefold() not in f.casefold():continue
     rel=(Path(base)/f).relative_to(root).as_posix()
     try:
      p=self.path(alias+'/'+rel)
      if p.is_file():rows.append(alias+'/'+rel)
     except ValueError:continue
     if len(rows)>=40:return rows+['[Dastlabki 40 natija]']
  return rows
 def read_bytes(self,name,limit=LIMIT):
  p=self.path(name)
  with p.open('rb') as f:data=f.read(limit+1)
  if len(data)>limit:raise ValueError('Fayl hajmi limitdan katta')
  return data
 def text(self,name):
  data=self.read_bytes(name,256*1024)
  if is_binary(self.path(name),data):raise ValueError('Faqat UTF-8 matn tahriri; Word/PDF uchun /pcget ishlating')
  try:return data.decode('utf-8')
  except UnicodeError:raise ValueError('Fayl UTF-8 matn emas') from None
 def propose(self,name,old,new):
  if len(old)>1000 or len(new)>1000:raise ValueError('Tahrir ko‘rinishi uchun eski/yangi matn 1000 belgidan oshmasin')
  before=self.text(name)
  if not old or before.count(old)!=1:raise ValueError('Eski matn faylda aynan bir marta uchrashi kerak')
  after=before.replace(old,new,1)
  if len(after.encode('utf8'))>256*1024:raise ValueError('Matn limiti')
  self.pending={k:v for k,v in self.pending.items() if v['expires']>time.time()}
  if len(self.pending)>=20:raise ValueError('Tahrirlar navbati to‘la; 5 daqiqa kuting')
  token=secrets.token_hex(6);v={'token':token,'name':name,'digest':hashlib.sha256(before.encode()).hexdigest(),'after':after,'expires':time.time()+300}
  self.pending[token]=v;return v
 def apply(self,token):
  v=self.pending.pop(token,None)
  if not v or v['expires']<time.time():raise ValueError('Tahrir kodi eskirgan yoki ishlatilgan')
  p=self.path(v['name']);data=self.read_bytes(v['name'],256*1024)
  if hashlib.sha256(data).hexdigest()!=v['digest']:raise ValueError('Fayl o‘zgargan; yangi tahrir tayyorlang')
  backup=self.state/'file_backups';backup.mkdir(parents=True,exist_ok=True)
  (backup/(str(int(time.time()))+'_'+token+'_'+p.name)).write_bytes(data)
  tmp=p.with_name('.agentlar-'+token+'.tmp')
  try:
   with tmp.open('xb') as f:f.write(v['after'].encode('utf8'));f.flush();os.fsync(f.fileno())
   os.replace(tmp,p)
  finally:tmp.unlink(missing_ok=True)
  return v['name']
