"""Render free web service with persistent Neon data and owner-only Telegram webhook."""
import hmac
import json
import os
import threading
from hosted_vault import accepted_text
from agentlar.api import Telegram
from zaxira.bot import VaultCommands
from zaxira.postgres import PostgresVault
from zaxira.receiver import Server

def main():
    secret=os.environ['WEBHOOK_SECRET']
    key=os.environ['VAULT_MASTER_KEY']
    if min(len(secret),len(key))<32: raise RuntimeError('Kamida 32 belgili alohida sirlar kerak')
    owner=int(os.environ['TELEGRAM_OWNER_ID'])
    tg=Telegram(os.environ['TELEGRAM_BOT_TOKEN'],owner)
    vault=PostgresVault(owner,os.environ['DATABASE_URL'],key)
    with Server(vault,int(os.environ.get('PORT','10000')),host='0.0.0.0') as server:
        commands=VaultCommands(server,tg)
        lock=threading.Lock()
        recent=set()
        def webhook(handler):
            header=handler.headers.get('X-Telegram-Bot-Api-Secret-Token','')
            if not hmac.compare_digest(secret.encode(),header.encode()): raise PermissionError()
            update=json.loads(handler.read_body(65536))
            text=accepted_text(update.get('message',{}),owner)
            with lock:
                ident=int(update['update_id'])
                if text and ident not in recent:
                    try:
                        if not commands.handle(text): tg.send('/zhelp — zaxira buyruqlari')
                    except ValueError: tg.send('Amal bajarilmadi. /zhelp orqali tekshiring.')
                    if len(recent)>2048: recent.clear()
                    recent.add(ident)
            handler.reply(200,{'ok':True})
        server.webhook=webhook
        base=os.environ['RENDER_EXTERNAL_URL'].rstrip('/')
        if not base.startswith('https://'): raise ValueError('HTTPS kerak')
        tg.call('setWebhook',{'url':base+'/telegram','secret_token':secret,'allowed_updates':['message'],'max_connections':1})
        server.serve_forever()

if __name__=='__main__': main()
