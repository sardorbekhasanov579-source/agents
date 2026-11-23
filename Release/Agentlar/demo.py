"""Offline smoke demo. No AI/API calls and no credentials."""
import tempfile
from pathlib import Path
from agentlar.engine import Engine

class DemoAI:
    def __init__(self):
        self.steps=iter([
            {'plan':'Namoyish uchun sodda HTML sahifa yaratish.'},
            {'action':'write','path':'index.html','text':'<!doctype html><html lang="uz"><meta charset="utf-8"><title>Agentlar demo</title><h1>Salom, Sardor!</h1><p>Bu offline sinov fayli.</p></html>'},
            {'action':'write','path':'README.md','text':'Offline demo. index.html ni brauzerda oching.'},
            {'action':'finish','summary':'Offline namuna yozildi; bu haqiqiy Gemini javobi emas.'},
            {'ok':True,'issues':[],'summary':'Demo tekshiruv javobi — haqiqiy AI tekshiruvi emas.'}])
    def ask(self,*args,**kwargs): return next(self.steps)

if __name__=='__main__':
    with tempfile.TemporaryDirectory() as d:
        e=Engine(Path(d),{'sources':{},'max_steps':8,'allow_local_build':True},DemoAI(),print)
        j=e.create('Demo HTML'); e.run(j['id'])
        saved=e.store.load(j['id'])
        assert saved['status']=='done'
        assert Path(saved['archive']).exists()
        print('\nOFFLINE DEMO OK. Telegram/Gemini ulanishi bu testda tekshirilmagan.')
