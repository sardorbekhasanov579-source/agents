import time
from pathlib import Path
from .core import authorized

HELP='''AGENTLAR — shaxsiy AI jamoangiz
Oddiy matn yuboring: yangi topshiriq boshlanadi.
/status — vazifalar holati
/stop — faol ishni to‘xtatish
/resume ID — saqlangan ishni davom ettirish
/change ID yangi talab — mavjud loyihani o‘zgartirish
/files ID — loyiha ZIP fayli
/sources — ruxsat etilgan manbalar
/doctor — kompyuter va build imkoniyatlari
/search savol — internetdan izlab hujjat tayyorlash
/approve ID KOD — ko‘rsatilgan host buyrug‘iga ruxsat
/reject ID — host buyrug‘ini rad etish
/zhelp — shaxsiy hujjatlar zaxirasi (8_ZAXIRA_START.bat)
/devices — kompyuter va telefon fayllari
/help — yordam

V1 matnli topshiriqlarni qabul qiladi. Kompyuter va internet yoqilgan bo‘lsin. Model chaqiruvlari API kvotasini ishlatadi.'''

class Bot:
    def __init__(self,config,engine,tg,phone=None,vault=None):
        self.vault=vault
        self.config=config; self.engine=engine; self.tg=tg
        from .device_commands import DeviceCommands
        self.devices=DeviceCommands(config,getattr(engine,'base',Path('.')),tg,phone)

    def handle(self,message):
        if not authorized(message,self.config['owner_id']): return
        text=message.get('text','').strip()
        try:
            if not text:
                self.tg.send('V1 da matnli topshiriq yuboring. Fayllarni ruxsat etilgan manba papkasiga qo‘ying.'); return
            if self.vault and self.vault.handle(text): return
            if not self.vault and text.split()[0].split('@')[0] in ('/zhelp','/zpair','/zaxira','/zfind','/zoff','/zol'):
                self.tg.send('Zaxira uchun botni 8_ZAXIRA_START.bat bilan oching.'); return
            if self.devices.handle(text): return
            parts=text.split(); command=parts[0].split('@')[0]
            e=self.engine
            if command in ('/start','/help'): self.tg.send(HELP)
            elif command=='/status':
                rows=e.store.jobs()[:10]
                self.tg.send('\n\n'.join(j['id']+'\n'+j['status']+' | AI murojaatlari: '+str(j['calls'])+'\nBosqich: '+j.get('phase','—')+' | Qadam: '+str(j.get('step',0))+'/'+str(j.get('step_limit','—'))+'\n'+j['task'][:180] for j in rows) or 'Hali vazifa yo‘q.')
            elif command=='/search' and len(parts)>=2:
                if e.busy(): raise ValueError('Avval faol vazifa tugasin yoki /stop bering')
                task='Internetdan search amali orqali tekshir, manba havolalari bilan Markdown hujjat yoz: '+text.split(maxsplit=1)[1]
                job=e.create(task); e.start(job['id']); self.tg.send('Qidiruv vazifasi: '+job['id'])
            elif command=='/stop':
                e.stop(); self.tg.send('To‘xtatish so‘rovi olindi. Joriy API so‘rovi qaytgach yangi amal bajarilmaydi.')
            elif command=='/sources': self.tg.send('Manba nomlari: '+', '.join(self.config.get('sources',{}))+'\nO‘qilgan matn Gemini API ga yuboriladi.')
            elif command=='/doctor':
                import shutil,sys,platform
                self.tg.send('Tizim: '+platform.system()+'\nPython: '+sys.version.split()[0]+'\nNode: '+('bor' if shutil.which('node') else 'yo‘q')+'\nnpm: '+('bor' if shutil.which('npm') else 'yo‘q')+'\nWSL: '+('bor (bu versiya Windowsda build qiladi)' if shutil.which('wsl') else 'aniqlanmadi')+'\nLocal build: '+('yoqilgan' if self.config.get('allow_local_build') else 'o‘chiq — 4_LOCAL_BUILD_SOZLASH.bat')+'\nGemini: '+self.config.get('model','—')+'\nAPI oralig‘i: '+str(self.config.get('gemini_min_interval',15))+' soniya\nKompyuter/telefon fayllari: /devices. Telefon ekranini boshqarish yo‘q.')
            elif command=='/resume' and len(parts)==2:
                j=e.store.load(parts[1])
                if j['status']=='done': self.tg.send('Vazifa tugagan. O‘zgartirish uchun /change ID yangi talab.'); return
                e.start(parts[1]); self.tg.send('Davom ettirilmoqda: '+parts[1])
            elif command=='/change' and len(parts)>=3:
                if e.busy(): raise ValueError('Avval faol ish tugasin yoki /stop bering')
                j=e.store.load(parts[1]); addition=text.split(maxsplit=2)[2]
                if len(j['task'])+len(addition)>16000: raise ValueError('Topshiriq uzunligi limiti')
                j['task']+='\nYangi talab: '+addition; j['plan']=None; j['pending']=None; j['status']='paused'
                e.store.save(j['id'],j); e.start(j['id'])
            elif command=='/files' and len(parts)==2:
                j=e.store.load(parts[1])
                if e.busy() and e.active==j['id']: raise ValueError('Fayllar yozilmoqda; avval /stop yoki tugashini kuting')
                w=e.workspace(j['id'])
                if not w.list_files(): raise ValueError('Hali fayl yaratilmagan')
                from .build import valid_evidence
                build=j.get('build',{})
                if j['status']=='done' and valid_evidence(w,build):
                    self.tg.document(j['archive'])
                else: self.tg.document(w.archive(e.base/'exports'/(j['id']+'.zip')))
            elif command=='/approve' and len(parts)==3: e.approve(parts[1],parts[2])
            elif command=='/reject' and len(parts)==2: e.reject(parts[1])
            elif text.startswith('/'): self.tg.send('Buyruq formati noto‘g‘ri. /help')
            else:
                if e.busy(): raise ValueError('Hozir bitta vazifa bajarilmoqda. /status yoki /stop')
                job=e.create(text); e.start(job['id']); self.tg.send('Vazifa qabul qilindi: '+job['id'])
        except Exception as exc: self.tg.send('Xato: '+self.engine.redact(str(exc))[:1000])

    def poll(self):
        s=self.engine.store
        try: offset=s.load('telegram_offset')['offset']
        except FileNotFoundError: offset=0
        self.tg.call('deleteWebhook', {'drop_pending_updates':False})
        self.tg.send('Agentlar ishga tushdi. /help')
        while True:
            try:
                updates=self.tg.call('getUpdates',{'offset':offset,'timeout':30,'allowed_updates':['message']},timeout=45)
                for update in updates:
                    # Persist before dispatch: avoid duplicate execution after a crash.
                    offset=update['update_id']+1; s.save('telegram_offset',{'offset':offset})
                    self.handle(update.get('message',{}))
            except KeyboardInterrupt:
                self.engine.stop(); return
            except Exception:
                print('Telegram bilan ulanishda xato. 5 soniyadan keyin qayta uriniladi.'); time.sleep(5)
