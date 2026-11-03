import sqlite3
import json
from pathlib import Path

def connect(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path)
    db.execute('''CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY,game_id TEXT NOT NULL, model_version TEXT NOT NULL,created_at TEXT NOT NULL,data_cutoff TEXT NOT NULL,kickoff TEXT NOT NULL,home_probability REAL NOT NULL,official INTEGER NOT NULL,payload TEXT NOT NULL,result REAL)''')
    db.execute('CREATE UNIQUE INDEX IF NOT EXISTS one_official ON predictions(game_id) WHERE official=1')
    db.execute('''CREATE TRIGGER IF NOT EXISTS immutable_forecast BEFORE UPDATE OF game_id,model_version,created_at,data_cutoff,kickoff,home_probability,official,payload ON predictions BEGIN SELECT RAISE(ABORT,'Forecasts are immutable'); END''')
    db.execute('''CREATE TABLE IF NOT EXISTS models(version TEXT PRIMARY KEY,metadata TEXT NOT NULL)''')
    return db

def insert(db,record):
    import pandas as pd
    if pd.Timestamp(record['created_at']) >= pd.Timestamp(record['kickoff']) or pd.Timestamp(record['data_cutoff']) > pd.Timestamp(record['created_at']):
        raise ValueError('Official/revised forecast must be issued before kickoff with a valid cutoff')
    with db:
        official=int(db.execute('SELECT 1 FROM predictions WHERE game_id=? AND official=1',(record['game_id'],)).fetchone() is None)
        db.execute('INSERT INTO predictions(game_id,model_version,created_at,data_cutoff,kickoff,home_probability,official,payload) VALUES(?,?,?,?,?,?,?,?)',tuple(record[k] for k in ['game_id','model_version','created_at','data_cutoff','kickoff','home_probability'])+(official,json.dumps(record)))
    return official

def attach_results(db,schedules):
    with db:
        for g in schedules[schedules.completed].itertuples():
            result=.5 if g.home_score==g.away_score else float(g.home_score>g.away_score)
            db.execute('UPDATE predictions SET result=? WHERE game_id=?',(result,g.game_id))
