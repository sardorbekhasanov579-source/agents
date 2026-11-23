from .document_text import EXTENSIONS, extract
import json
import contextlib
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import unicodedata
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAX_FILE = 10 * 1024 * 1024
MAX_STORE = 512 * 1024 * 1024
MAX_ITEMS = 1000

def safe_name(name):
    if not isinstance(name, str) or not name.strip() or len(name.encode('utf-8')) > 240:
        raise ValueError('Fayl nomi yaroqsiz')
    if any(c in '/\\' or unicodedata.category(c).startswith('C') for c in name):
        raise ValueError('Fayl nomida ruxsat etilmagan belgi')
    return name

def search_words(query):
    words = re.findall(r'[^\W_]+', query.casefold())
    words = [re.sub(r'(?:larimni|imni|larni|ni)$', '', w) if len(w)>4 else w for w in words]
    return [w for w in words if w and w not in {'hujjat','hujjatlar','fayl','fayllar','menga','mening','iltimos'}]

class Vault:
    @property
    def quota(self):
        return MAX_STORE
    blob_type = "BLOB"
    tie_breaker = "rowid"

    def lock_upload(self, db):
        db.execute('BEGIN IMMEDIATE')

    def recovery_record(self):
        path = self.db.parent / 'recovery.json'
        return json.loads(path.read_text(encoding='utf8')) if path.exists() else None

    def create_recovery(self, record):
        with (self.db.parent / 'recovery.json').open('x',encoding='utf8') as stream:
            json.dump(record,stream)

    def __init__(self, directory, owner):
        self.owner = str(int(owner))
        directory = Path(directory)
        directory.mkdir(parents=True, mode=0o700, exist_ok=True)
        self.db = directory / 'vault.sqlite3'
        keyfile = directory / 'vault.key'
        if not keyfile.exists():
            if self.db.exists():
                raise ValueError('vault.key topilmadi. Avvalgi kalitni asl nusxasidan tiklang.')
            with os.fdopen(os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),'wb') as f:
                f.write(secrets.token_bytes(32))
                f.flush()
                os.fsync(f.fileno())
        key = keyfile.read_bytes()
        self.initialize(key)

    def initialize(self, key):
        self.cipher = AESGCM(key)
        self.index_key = hmac.digest(key, b'zaxira/content-index/v1', 'sha256')
        with self.connection() as db:
            db.execute(f'CREATE TABLE IF NOT EXISTS vault_info (slot INTEGER PRIMARY KEY, check_value {self.blob_type} NOT NULL)')
            check_value=hmac.digest(key,b'zaxira/key-check/v1','sha256')
            db.execute('INSERT INTO vault_info VALUES(1,?) ON CONFLICT(slot) DO NOTHING',(check_value,))
            saved=db.execute('SELECT check_value FROM vault_info WHERE slot=1').fetchone()[0]
            if not hmac.compare_digest(saved,check_value):
                raise ValueError('vault.key ushbu omborga mos emas. Asl kalitni tiklang.')
            db.execute(f'CREATE TABLE IF NOT EXISTS items (id TEXT PRIMARY KEY, owner TEXT NOT NULL, signature {self.blob_type}, stamp BIGINT, size INTEGER, title {self.blob_type}, data {self.blob_type}, UNIQUE(owner,signature))')
    @contextlib.contextmanager
    def connection(self):
        with contextlib.closing(sqlite3.connect(self.db, timeout=10)) as db:
            with db:
                yield db
    def seal(self, ident, label, data):
        nonce=secrets.token_bytes(12)
        return nonce+self.cipher.encrypt(nonce,data,f'{self.owner}:{ident}:{label}'.encode())
    def unseal(self, ident, label, encrypted):
        return self.cipher.decrypt(encrypted[:12],encrypted[12:],f'{self.owner}:{ident}:{label}'.encode())
    def encode_file(self, ident, name, body):
        return self.seal(ident,'file',body)

    def decode_file(self, ident, data):
        return self.unseal(ident,'file',data)

    def add(self, name, body):
        name=safe_name(name)
        if len(body)>MAX_FILE:
            raise ValueError('Limit 10 MiB')
        signature=hmac.digest(self.index_key, name.encode()+b'\0'+hashlib.sha256(body).digest(),'sha256')
        with self.connection() as db:
            self.lock_upload(db)
            row=db.execute('SELECT id FROM items WHERE owner=? AND signature=?',(self.owner,signature)).fetchone()
            if row:
                return row[0],False
            count,total=db.execute('SELECT count(*),coalesce(sum(size),0) FROM items WHERE owner=?',(self.owner,)).fetchone()
            if count>=MAX_ITEMS or total+len(body)>self.quota:
                raise ValueError('Zaxira limiti to‘ldi.')
            ident=signature.hex()[:16]
            db.execute('INSERT INTO items VALUES (?,?,?,?,?,?,?)',(ident,self.owner,signature,int(time.time()),len(body),self.seal(ident,'name',name.encode()),self.encode_file(ident,name,body)))
            if hasattr(self,'search_excerpt') and name.lower().endswith(EXTENSIONS) and len(body)<=2*1024*1024:
                snippet=extract(name,body)[:32768].encode()
                db.execute('INSERT INTO zaxira_excerpt VALUES (?,?,?)',(self.owner,ident,self.seal(ident,'excerpt',snippet)))
        return ident,True
    def search(self, query, limit=10, *, start=0, end=2**63-1):
        words=search_words(query)
        found=[]
        with self.connection() as db:
            for ident,stamp,size,title in db.execute(f'SELECT id,stamp,size,title FROM items WHERE owner=? AND stamp>=? AND stamp<? ORDER BY stamp DESC,{self.tie_breaker} DESC',(self.owner,start,end)):
                name=self.unseal(ident,'name',title).decode()
                searchable = name.casefold()
                if (words and not all(w in searchable for w in words)
                        and size <= 2 * 1024 * 1024 and searchable.endswith(EXTENSIONS)):
                    encrypted = db.execute('SELECT data FROM items WHERE id=? AND owner=?',
                                           (ident, self.owner)).fetchone()[0]
                    content = extract(name,self.decode_file(ident,encrypted)) if encrypted else self.search_excerpt(db,ident)
                    searchable += ' ' + content.casefold()
                if all(w in searchable for w in words):
                    found.append((ident,name,size,stamp))
                    if len(found)>=limit: break
        return found
    def get(self, ident):
        with self.connection() as db:
            row=db.execute('SELECT title,data FROM items WHERE id=? AND owner=?',(ident,self.owner)).fetchone()
        if not row:
            raise ValueError('Bu hisobda bunday fayl yo‘q')
        return self.unseal(ident,'name',row[0]).decode(),self.decode_file(ident,row[1])
