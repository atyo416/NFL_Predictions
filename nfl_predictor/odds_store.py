"""Dedicated M8 SQLite store. Append-only rows; immutable prior milestones."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import sqlite3

TABLES=['raw','quotes','receipts','matches','forecasts','strategies','wagers','events']


def utc_now():return datetime.now(timezone.utc)


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False,default=str)


def key(value):return hashlib.sha256(encoded(value).encode()).hexdigest()


def connect(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30);db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    for table in TABLES:
        if table=='raw':db.execute('CREATE TABLE IF NOT EXISTS raw(id TEXT PRIMARY KEY,content BLOB NOT NULL)')
        elif table=='wagers':db.execute('CREATE TABLE IF NOT EXISTS wagers(id TEXT PRIMARY KEY,slot TEXT UNIQUE NOT NULL,created_at TEXT NOT NULL,payload TEXT NOT NULL)')
        else:db.execute(f'CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,payload TEXT NOT NULL)')
        for action in ['UPDATE','DELETE']:
            db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'M8 records are append-only'); END")
    db.commit();return db


def append(db,table,payload,identifier=None,ignore_fields=()):
    if table not in TABLES or table in ['raw','wagers']:raise ValueError('Unsupported append table')
    identifier=identifier or key(payload)
    existing=db.execute(f'SELECT payload FROM {table} WHERE id=?',(identifier,)).fetchone()
    if existing:
        old=json.loads(existing['payload'])
        if {k:v for k,v in old.items() if k not in ignore_fields}!={k:v for k,v in payload.items() if k not in ignore_fields}:raise ValueError('Immutable M8 identity already has different content')
        return old
    db.execute(f'INSERT INTO {table} VALUES(?,?,?)',(identifier,str(payload.get('created_at',utc_now().isoformat())),encoded(payload)))
    return payload


def rows(db,table):
    if table not in TABLES or table=='raw':raise ValueError('Unsupported read table')
    return [json.loads(r['payload']) for r in db.execute(f'SELECT payload FROM {table} ORDER BY created_at,id')]


def read_only_rows(path,table):
    path=Path(path)
    if not path.exists():return []
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:return rows(db,table)
    finally:db.close()
