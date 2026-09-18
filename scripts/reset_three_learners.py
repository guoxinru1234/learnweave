import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

db = Path('backend/data/learnmate.db')
backup = db.with_name(f'learnmate-before-reset-{datetime.now():%Y%m%d-%H%M%S}.db')
shutil.copy2(db, backup)

usernames = ('learner_a', 'learner_b', 'learner_c')
conn = sqlite3.connect(db)
conn.execute('PRAGMA foreign_keys = ON')
ids = {
    name: conn.execute('SELECT id FROM users WHERE username = ?', (name,)).fetchone()[0]
    for name in usernames
}

candidate_tables = [
    'learner_profiles', 'user_profiles', 'chat_history', 'chat_feedback',
    'learning_records', 'daily_tasks', 'notes', 'quiz_attempts',
    'quiz_records', 'learning_progress', 'learning_events', 'interactions',
]

existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
deleted = {}
for table in candidate_tables:
    if table not in existing:
        continue
    columns = {row[1] for row in conn.execute(f'PRAGMA table_info({table})')}
    if 'user_id' not in columns:
        continue
    marks = ','.join('?' for _ in ids)
    before = conn.total_changes
    conn.execute(f'DELETE FROM {table} WHERE user_id IN ({marks})', tuple(ids.values()))
    deleted[table] = conn.total_changes - before

conn.commit()
conn.close()
print('backup:', backup)
print('accounts preserved:', ', '.join(usernames))
for table, count in deleted.items():
    print(f'{table}: {count}')
