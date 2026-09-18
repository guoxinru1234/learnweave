from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from ..core.database import get_connection
router=APIRouter(prefix='/community',tags=['community'])
class Post(BaseModel):
    content:str
    author:str='学习者'
def ensure_table():
    with get_connection() as c:
        c.execute('CREATE TABLE IF NOT EXISTS community_posts (id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'); c.commit()
@router.get('/')
def list_posts():
    ensure_table()
    with get_connection() as c:return [dict(r) for r in c.execute('SELECT id,author,content,created_at FROM community_posts ORDER BY id DESC').fetchall()]
@router.post('/')
def create_post(post:Post):
    ensure_table()
    with get_connection() as c:
        cur=c.execute('INSERT INTO community_posts(author,content,created_at) VALUES (?,?,?)',(post.author,post.content,datetime.utcnow().isoformat())); c.commit(); return {'id':cur.lastrowid,'author':post.author,'content':post.content}
