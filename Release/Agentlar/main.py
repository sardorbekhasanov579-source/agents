import os
import sys
from pathlib import Path
from agentlar.api import Gemini, Telegram
from agentlar.config import load_config
from agentlar.engine import Engine
from agentlar.bot import Bot

BASE=Path(__file__).resolve().parent

def main():
    if sys.version_info<(3,11): raise ValueError('Python 3.11 yoki yangiroq kerak')
    # OS lock is automatically released on crash; unlike a stale PID file.
    lock=(BASE/'agentlar.lock').open('a+b'); lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError: raise ValueError('Agentlar boshqa oynada ishga tushgan. Faqat bitta nusxani ishlating.') from None
    config=load_config(BASE)
    awake=None
    if os.name=='nt' and config.get('keep_awake',False):
        import ctypes
        awake=ctypes.windll.kernel32.SetThreadExecutionState
        awake.argtypes=[ctypes.c_uint32]; awake.restype=ctypes.c_uint32
        if not awake(0x80000001): print('Avtomatik uyquni to‘xtatish imkoni bo‘lmadi; Windows quvvat sozlamalarini tekshiring.')
    tg=Telegram(config['telegram_token'],config['owner_id'])
    ai=Gemini(config['gemini_api_key'],config['model'])
    engine=Engine(BASE,config,ai,tg.send,deliver=tg.document)
    print('AGENTLAR ISHLAMOQDA | Model: '+config['model'])
    print('Telegramda botingizga yozing. Ushbu oynani ochiq qoldiring. To‘xtatish: Ctrl+C')
    phone=None
    if config.get('phone_enabled',False):
        from agentlar.phone import PhoneBridge
        phone=PhoneBridge(BASE,tg.send,tg.document)
        phone.start()
        print('Telefon relay: 127.0.0.1:8765. Tunnel uchun 7_TELEFON_INTERNET.bat')
    vault_server=None
    vault_commands=None
    if os.environ.get('AGENTLAR_BACKUP')=='1':
        import threading
        from zaxira.store import Vault
        from zaxira.receiver import Server
        from zaxira.bot import VaultCommands
        vault_server=Server(Vault(BASE/'private_backup',config['owner_id']))
        threading.Thread(target=vault_server.serve_forever,daemon=True).start()
        vault_commands=VaultCommands(vault_server,tg)
        print('Zaxira tayyor. Telegram: /zpair')
    try: Bot(config,engine,tg,phone,vault_commands).poll()
    finally:
        print('Yopilmoqda; faol so‘rov va jarayonlar tugashini kuting...')
        try:
            if vault_server:
                vault_server.shutdown()
                vault_server.server_close()
            if phone: phone.close()
            engine.shutdown()
        finally:
            if awake: awake(0x80000000)
            lock.close()

if __name__=='__main__':
    try: main()
    except Exception as e: print('Ishga tushmadi: '+str(e)); sys.exit(1)
