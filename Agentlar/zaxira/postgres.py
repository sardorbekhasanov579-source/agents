from contextlib import contextmanager
import hashlib
import json
import os
import psycopg
from .store import Vault


class Connection:
    def __init__(self, db):
        self.db=db

    def execute(self, sql, args=()):
        return self.db.execute(sql.replace('?', '%s'),args)


class PostgresVault(Vault):
    blob_type='BYTEA'
    tie_breaker='id'
    quota=4_800_000_000

    def __init__(self, owner, dsn, secret):
        self.owner=str(int(owner))
        self.dsn=dsn
        from .remote import Remote
        self.initialize(hashlib.sha256(secret.encode()).digest())
        with self.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS recovery_accounts(owner TEXT PRIMARY KEY, record TEXT NOT NULL)')

            db.execute('CREATE TABLE IF NOT EXISTS zaxira_excerpt(owner TEXT, id TEXT, snippet BYTEA, PRIMARY KEY(owner,id))')
        self.remote=Remote(self,os.environ['ZAXIRA_REMOTE_CONFIG'])

    def encode_file(self,ident,name,body):
        self.remote.transfer(ident,self.seal(ident,'file',body))
        return b''

    def decode_file(self,ident,data):
        return self.unseal(ident,'file',data or self.remote.transfer(ident))

    def search_excerpt(self,db,ident):
        row=db.execute('SELECT snippet FROM zaxira_excerpt WHERE owner=? AND id=?',(self.owner,ident)).fetchone()
        return self.unseal(ident,'excerpt',row[0]).decode() if row else ''

    @contextmanager
    def connection(self):
        with psycopg.connect(self.dsn,connect_timeout=10) as db:
            yield Connection(db)

    def lock_upload(self, db):
        db.execute('SELECT pg_advisory_xact_lock(?)',(int(self.owner),))

    def recovery_record(self):
        with self.connection() as db:
            row=db.execute('SELECT record FROM recovery_accounts WHERE owner=?',(self.owner,)).fetchone()
        return json.loads(row[0]) if row else None

    def create_recovery(self, record):
        with self.connection() as db:
            db.execute('INSERT INTO recovery_accounts VALUES (?,?)',(self.owner,json.dumps(record)))
