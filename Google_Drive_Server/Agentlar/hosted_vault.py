"""Single-owner backup service behind the hosting provider's HTTPS proxy."""
import os
import threading
import time
from pathlib import Path

from agentlar.api import Telegram
from zaxira.bot import VaultCommands
from zaxira.receiver import Server
from zaxira.store import Vault


def accepted_text(message, owner):
    chat = message.get('chat', {})
    if chat.get('type') == 'private' and chat.get('id') == owner and message.get('from', {}).get('id') == owner:
        return message.get('text', '').strip()
    return ''


def poll(server, tg):
    commands = VaultCommands(server, tg)
    checkpoint = server.vault.db.parent / 'telegram-offset'
    offset = int(checkpoint.read_text()) if checkpoint.exists() else 0
    while True:
        try:
            updates = tg.call('getUpdates', {'offset': offset, 'timeout': 20, 'allowed_updates': ['message']}, timeout=35)
            for update in updates:
                text = accepted_text(update.get('message', {}), tg.owner)
                if text:
                    try:
                        if not commands.handle(text):
                            tg.send('Zaxira buyruqlari uchun /zhelp yozing.')
                    except ValueError:
                        tg.send('Nusxa topilmadi yoki yuborilmadi. /zaxira orqali qayta tanlang.')
                offset = update['update_id'] + 1
                temp = checkpoint.with_suffix('.tmp')
                temp.write_text(str(offset))
                temp.replace(checkpoint)
        except Exception as error:
            print('Telegram ulanishi qayta tekshiriladi:', type(error).__name__, flush=True)
            time.sleep(5)


def main():
    owner = int(os.environ['TELEGRAM_OWNER_ID'])
    if owner <= 0:
        raise ValueError('TELEGRAM_OWNER_ID musbat son bo‘lishi kerak')
    tg = Telegram(os.environ['TELEGRAM_BOT_TOKEN'], owner)
    directory = Path(os.environ['ZAXIRA_DATA_DIR'])
    if not directory.is_absolute() or not directory.is_dir():
        raise RuntimeError('Doimiy diskni ZAXIRA_DATA_DIR manziliga ulang')
    vault = Vault(directory, owner)
    with Server(vault, int(os.environ.get('PORT', '8766')), host='0.0.0.0') as server:
        threading.Thread(target=poll, args=(server, tg), daemon=True).start()
        server.serve_forever()


if __name__ == '__main__':
    main()
