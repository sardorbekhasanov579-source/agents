"""Store only encrypted objects on the owner's rclone remote."""
import base64
import configparser
import os
from pathlib import Path
import subprocess
import tempfile
from threading import RLock

class Remote:
    def __init__(self,vault,encoded):
        self.vault=vault
        self.lock=RLock()
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'rclone.conf'
        config=base64.b64decode(encoded,validate=True)
        with vault.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS zaxira_remote_config (owner TEXT PRIMARY KEY, value BYTEA NOT NULL)')
            row=db.execute('SELECT value FROM zaxira_remote_config WHERE owner=?',(vault.owner,)).fetchone()
        if row: config=vault.unseal('remote','config',row[0])
        parser=configparser.ConfigParser(interpolation=None)
        parser.read_string(config.decode('utf-8-sig'))
        if parser.sections()!=['zaxira'] or parser['zaxira'].get('type') not in ('onedrive','drive','s3'):
            raise ValueError('Faqat zaxira nomli onedrive, drive yoki s3 remote kerak')
        self.prefix='zaxira:'+('' if parser['zaxira']['type']!='s3' else os.environ['ZAXIRA_BUCKET']+'/')+'ShaxsiyZaxira/'+vault.owner+'/'
        self.path.write_bytes(config)
        self.path.chmod(0o600)

    def transfer(self,ident,payload=None):
        target=self.prefix+ident+'.bin'
        command=['rclone','--config',str(self.path),'--retries','2','--low-level-retries','2',
                 'cat' if payload is None else 'rcat',target]
        with self.lock:
            before=self.path.read_bytes()
            try:
                result=subprocess.run(command,input=payload,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=110)
                if result.returncode: raise OSError('Bulut omboriga ulanish yoki kvota xatosi')
                return result.stdout
            finally:
                updated=self.path.read_bytes()
                if updated!=before:
                    with self.vault.connection() as db:
                        db.execute('INSERT INTO zaxira_remote_config VALUES (?,?) ON CONFLICT(owner) DO UPDATE SET value=excluded.value',
                                   (self.vault.owner,self.vault.seal('remote','config',updated)))
