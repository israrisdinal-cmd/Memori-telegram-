# api.py - FastAPI untuk Mini App
# pip install fastapi uvicorn psycopg2-binary python-telegram-bot
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import psycopg2.extras

DB_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DB_URL)
conn.autocommit = True

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def dict_cur():
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

@app.get("/onthisday")
def onthisday(month: int, day: int):
    cur = dict_cur()
    cur.execute("""
      SELECT file_id, caption, taken_at, message_id, chat_id
      FROM photos
      WHERE EXTRACT(month FROM taken_at)=%s AND EXTRACT(day FROM taken_at)=%s
      ORDER BY taken_at DESC
    """, (month, day))
    return cur.fetchall()

@app.get("/people")
def people():
    cur = dict_cur()
    cur.execute("""
      SELECT cluster_id, COALESCE(person_name, 'Orang ' || (cluster_id+1)) as name, COUNT(*) as count
      FROM faces WHERE cluster_id >= 0
      GROUP BY cluster_id, person_name
      ORDER BY count DESC
    """)
    return cur.fetchall()

@app.get("/people/{cluster_id}")
def people_photos(cluster_id: int):
    cur = dict_cur()
    cur.execute("""
      SELECT DISTINCT p.file_id, p.caption, p.taken_at
      FROM faces f JOIN photos p ON p.file_id = f.file_id
      WHERE f.cluster_id = %s ORDER BY p.taken_at DESC
    """, (cluster_id,))
    return cur.fetchall()
