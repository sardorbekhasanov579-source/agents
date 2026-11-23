import base64
from pathlib import Path
from .devices import PCFiles
DEVICE_HELP='''QURILMALAR (faqat o‘zingizning shaxsiy chattingizda)
/pcroots — tanlangan kompyuter papkalari
/pcfind so‘z — fayl nomidan qidirish
/pcget hujjat/fayl.pdf — faylni olish (4 MiB)
/pcread hujjat/fayl.txt — UTF-8 matn
/pcedit hujjat/fayl.txt | eski matn | yangi matn — tahrir loyihasi
/pcapply KOD — zaxira saqlab tahrirni qo‘llash
/phonepair — telefonga bir martalik kod (5 daqiqa)
/phone — telefon holati
/phonefind so‘z — tanlangan telefon papkasida qidirish
/phoneget FAYL_ID — qidiruvdagi faylni Telegramga olish
/phoneput hujjat/fayl.pdf — kompyuterdan telefonga yangi nusxa
/phoneoff — telefon ruxsatini bekor qilish
Telefon ekrani va boshqa ilovalarni bosib boshqarish bu versiyada yo‘q.'''
class DeviceCommands:
 def __init__(self,config,base,tg,phone=None):
  self.pc=PCFiles(config.get('pc_folders',{}),Path(base)/'state');self.tg=tg;self.phone=phone;self.base=Path(base)
 def handle(self,text):
  cmd,_,arg=text.partition(' ');cmd=cmd.split('@')[0];arg=arg.strip()
  if cmd=='/devices':self.tg.send(DEVICE_HELP)
  elif cmd=='/pcroots':self.tg.send('Papka nomlari: '+(', '.join(self.pc.roots) or 'yo‘q — 5_PC_PAPKA_SOZLASH.bat'))
  elif cmd=='/pcfind':
   if not arg:raise ValueError('/pcfind qidiriladigan_so‘z')
   self.tg.send('\n'.join(self.pc.find(arg)) or 'Topilmadi')
  elif cmd=='/pcget':
   data=self.pc.read_bytes(arg);out=self.base/'exports'/'personal';out.mkdir(parents=True,exist_ok=True)
   import secrets
   p=out/(secrets.token_hex(4)+'_'+self.pc.path(arg).name);p.write_bytes(data);self.tg.document(p)
  elif cmd=='/pcread':self.tg.send(self.pc.text(arg)[:8000] or '(bo‘sh)')
  elif cmd=='/pcedit':
   fields=arg.split(' | ',2)
   if len(fields)!=3:raise ValueError('/pcedit hujjat/fayl.txt | eski matn | yangi matn')
   v=self.pc.propose(fields[0],fields[1],fields[2]);self.tg.send('Fayl: '+fields[0]+'\nEski: '+fields[1][:1000]+'\nYangi: '+fields[2][:1000]+'\nZaxira bilan qo‘llash (5 daqiqa): /pcapply '+v['token'])
  elif cmd=='/pcapply':self.tg.send('Tahrirlandi, zaxira saqlandi: '+self.pc.apply(arg))
  elif cmd in ('/phone','/phonepair','/phonefind','/phoneget','/phoneput','/phoneoff'):
   if not self.phone:raise ValueError('Telefon moduli o‘chiq. 6_TELEFON_SOZLASH.bat ni ishga tushiring va botni qayta oching.')
   if cmd=='/phone':self.tg.send(self.phone.status())
   elif cmd=='/phonepair':self.tg.send('Ilovaga tunnel HTTPS manzili va kodni kiriting. Kod 5 daqiqa amal qiladi; boshqalarga bermang:\n'+self.phone.new_pair())
   elif cmd=='/phoneoff':self.phone.revoke();self.tg.send('Telefon ulanishi bekor qilindi; navbat tozalandi.')
   else:
    if not arg:raise ValueError('Buyruq argumenti kerak. /devices')
    if cmd=='/phonefind':ident=self.phone.enqueue('search',query=arg[:100])
    elif cmd=='/phoneget':ident=self.phone.enqueue('get',file_id=arg[:100])
    else:
     data=self.pc.read_bytes(arg);ident=self.phone.enqueue('put',name=self.pc.path(arg).name,data=base64.b64encode(data).decode())
    self.tg.send('Telefon navbatiga qo‘shildi: '+ident+'\nTelefon internetda va ilovada ulanish yoqilgan bo‘lsin. Amal 5 daqiqadan keyin eskiradi.')
  else:return False
  return True
