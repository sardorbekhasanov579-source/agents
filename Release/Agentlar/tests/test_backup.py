"""Exercise the phone protocol and real Telegram dispatcher without external credentials."""
import base64
import concurrent.futures
import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from cryptography.exceptions import InvalidTag
from agentlar.bot import Bot
from zaxira.bot import VaultCommands
from zaxira.receiver import Server
from zaxira.store import Vault, MAX_FILE

class TelegramCapture:
    def __init__(self):
        self.messages=[]
        self.files=[]
    def send(self, text):
        self.messages.append(text)

class MinimalEngine:
    def __init__(self, base):
        self.base=base
    def redact(self, text):
        return text

class BackupFlow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.vault=Vault(self.base/'private_backup',19)
        self.server=Server(self.vault,0)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.worker.start()
        self.addCleanup(self.close_server)
        self.tg=TelegramCapture()
        self.configure(self.server)
    def configure(self, server):
        self.commands=VaultCommands(server,self.tg,lambda n,b:self.tg.files.append((n,b)))
        self.bot=Bot({'owner_id':19},MinimalEngine(self.base),self.tg,vault=self.commands)
    def close_server(self):
        if self.worker.is_alive():
            self.server.shutdown()
            self.worker.join(2)
        self.server.server_close()
    def call(self, path, data=b'', extra=None):
        headers=extra or {}
        request=Request('http://127.0.0.1:'+str(self.server.server_port)+path,data=data,headers=headers)
        with urlopen(request,timeout=4) as response:
            return response.status,json.load(response)
    def message(self, text, owner=19, kind='private'):
        self.bot.handle({'from':{'id':owner},'chat':{'id':owner,'type':kind},'text':text})
    def pair(self):
        self.message('/zpair')
        code=self.tg.messages[-1].splitlines()[-1]
        return self.call('/v1/pair',json.dumps({'code':code}).encode())[1]['token']
    def upload(self, token, name, data, sha=None):
        return self.call('/v1/documents',data,{'Authorization':'Bearer '+token,'X-Name':base64.b64encode(name.encode()).decode(),'X-SHA256':sha or hashlib.sha256(data).hexdigest()})
    def test_select_upload_disconnect_restart_search_restore(self):
        token=self.pair()
        payload=b'%PDF-1.4\n\x00not UTF8\xff\x9f'
        name='Diplom – yakuniy.pdf'
        status,first=self.upload(token,name,payload)
        self.assertEqual(status,201)
        repeat,again=self.upload(token,name,payload)
        self.assertEqual((repeat,again['id']),(200,first['id']))
        self.message('/zoff')
        self.close_server()
        reopened=Vault(self.base/'private_backup',19)
        # No phone connection, no listener, same data on disk.
        class Offline:
            vault=reopened
        self.configure(Offline())
        self.message('Diplomimni top')
        self.assertIn(name,self.tg.messages[-1])
        command=self.tg.messages[-1].splitlines()[-1]
        self.message(command)
        self.assertEqual(self.tg.files,[(name,payload)])
        self.message('Hujjatimni top')
        self.assertIn(command,self.tg.messages[-1])
    def test_unpaired_expired_and_used_codes(self):
        self.message('/zpair');code=self.tg.messages[-1].splitlines()[-1]
        with patch('zaxira.receiver.time.monotonic',return_value=1e30),self.assertRaises(HTTPError) as e:
            self.call('/v1/pair',json.dumps({'code':code}).encode())
        self.assertEqual(e.exception.code,403)
        token=self.pair()
        with self.assertRaises(HTTPError):self.call('/v1/pair',json.dumps({'code':self.tg.messages[-1].splitlines()[-1]}).encode())
        self.message('/zoff')
        with self.assertRaises(HTTPError) as revoked:self.upload(token,'x',b'hi')
        self.assertEqual(revoked.exception.code,403)
    def test_other_chats_and_upload_token_cannot_read(self):
        token=self.pair()
        _,entry=self.upload(token,'Sirli.txt',b'egasi')
        before=len(self.tg.messages)
        self.message('/zpair',owner=20)
        self.message('/zol_'+entry['id'],owner=20)
        self.message('Hujjatimni top',kind='group')
        self.assertEqual(len(self.tg.messages),before)
        self.assertEqual(self.tg.files,[])
        with self.assertRaises(HTTPError) as e:self.call('/v1/get',entry['id'].encode(),{'Authorization':'Bearer '+token})
        self.assertEqual(e.exception.code,404)
        other=Vault(self.base/'private_backup',20)
        self.assertEqual(other.search(''),[])
        with self.assertRaises(ValueError):other.get(entry['id'])
    def test_encryption_integrity_and_missing_key(self):
        name='MyPrivateDiploma.txt'
        payload=b'Highly private test sample.'
        ident,_=self.vault.add(name,payload)
        raw=self.vault.db.read_bytes()
        self.assertNotIn(name.encode(),raw)
        self.assertNotIn(payload,raw)
        with sqlite3.connect(self.vault.db) as db:
            data=db.execute('select data from items').fetchone()[0]
            db.execute('update items set data=?',(data[:-1]+bytes([data[-1]^1]),))
        with self.assertRaises(InvalidTag):self.vault.get(ident)
        (self.vault.db.parent/'vault.key').unlink()
        with self.assertRaisesRegex(ValueError,'vault.key'):Vault(self.vault.db.parent,19)
    def test_wrong_key_fails_before_accepting_new_uploads(self):
        self.vault.add('reja.txt',b'X')
        key_path=self.vault.db.parent/'vault.key'
        key_path.write_bytes(b'Z'*32)
        with self.assertRaisesRegex(ValueError,'mos emas'):
            Vault(self.vault.db.parent,19)

    def test_changed_file_creates_version_and_clean_retry(self):
        token=self.pair()
        with self.assertRaises(HTTPError) as e:self.upload(token,'test.txt',b'contents','bad')
        self.assertEqual(e.exception.code,400)
        self.assertEqual(self.vault.search(''),[])
        first=self.upload(token,'test.txt',b'first')[1]['id']
        second=self.upload(token,'test.txt',b'second')[1]['id']
        self.assertNotEqual(first,second)
        self.assertEqual(self.vault.get(first)[1],b'first')
        self.assertEqual(self.vault.get(second)[1],b'second')
    def test_name_limit_file_and_quota(self):
        for name in ('','../x','line\r\nbreak.txt'):
            with self.assertRaises(ValueError):self.vault.add(name,b'x')
        with self.assertRaises(ValueError):self.vault.add('large',b'\0'*(MAX_FILE+1))
        with patch('zaxira.store.MAX_STORE',2):
            ident,_=self.vault.add('two',b'ab')
            with self.assertRaises(ValueError):self.vault.add('three',b'c')
            self.assertEqual(self.vault.add('two',b'ab'),(ident,False))
    def test_simultaneous_identical_uploads(self):
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            ids=list(pool.map(lambda _:self.vault.add('One.txt',b'1'),range(4)))
        self.assertEqual(sum(int(created) for _,created in ids),1)
        self.assertEqual(len(set(ident for ident,_ in ids)),1)
