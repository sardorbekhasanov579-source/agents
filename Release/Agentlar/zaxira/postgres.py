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
    quota=128*1024*1024

    def __init__(self, owner, dsn, secret):
        self.owner=str(int(owner))
        self.dsn=dsn
        self.initialize(hashlib.sha256(secret.encode()).digest())
        with self.connection() as db:
            db.execute('CREATE TABLE IF NOT EXISTS recovery_accounts(owner TEXT PRIMARY KEY, record TEXT NOT NULL)')

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
