import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

db=Path('backend/data/learnmate.db')
backup=db.with_name(f'learnmate-before-learner-a-reset-{datetime.now():%Y%m%d-%H%M%S}.db')
shutil.copy2(db,backup)
conn=sqlite3.connect(db)
row=conn.execute("SELECT id FROM users WHERE username='learner_a'").fetchone()
if not row: raise SystemExit('learner_a not found')
uid=row[0]
for table in ('learner_profiles','user_profiles','chat_history'):
    exists=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
    if exists: conn.execute(f'DELETE FROM {table} WHERE user_id=?',(uid,))
conn.commit(); conn.close()
print('backup:',backup)
print('learner_a profile and dialogue reset')
