# face_worker.py - Telegram Photo Face Grouping
# Metadata-only, foto tetap di Telegram
# pip install insightface onnxruntime numpy scikit-learn psycopg2-binary opencv-python requests
#
# Env yang dibutuhkan:
# BOT_TOKEN=...
# DATABASE_URL=postgresql://...
#
import os, json
import numpy as np
from sklearn.cluster import DBSCAN
import psycopg2
import requests
import insightface

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

face_app = insightface.app.FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

conn = psycopg2.connect(DB_URL)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS faces (
  id SERIAL PRIMARY KEY,
  file_id TEXT,
  message_id BIGINT,
  chat_id BIGINT,
  face_idx INT,
  embedding FLOAT8[],
  bbox JSONB,
  cluster_id INT,
  person_name TEXT,
  UNIQUE(file_id, face_idx)
);
CREATE INDEX IF NOT EXISTS faces_cluster_idx ON faces(cluster_id);
""")

def get_telegram_file_bytes(file_id: str) -> bytes:
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}", timeout=30)
    file_path = r.json()["result"]["file_path"]
    f = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}", timeout=60)
    return f.content

def process_photo(file_id, message_id, chat_id):
    try:
        img_bytes = get_telegram_file_bytes(file_id)
        nparr = np.frombuffer(img_bytes, np.uint8)
        import cv2
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        faces = face_app.get(img)
        for i, face in enumerate(faces):
            emb = face.normed_embedding.tolist()
            bbox = face.bbox.tolist()
            cur.execute("""
              INSERT INTO faces (file_id, message_id, chat_id, face_idx, embedding, bbox)
              VALUES (%s,%s,%s,%s,%s,%s)
              ON CONFLICT DO NOTHING
            """, (file_id, message_id, chat_id, i, emb, json.dumps(bbox)))
        return len(faces)
    except Exception as e:
        print("skip", file_id, e)
        return 0

def cluster_all():
    cur.execute("SELECT id, embedding FROM faces WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    if len(rows) < 2: return
    ids = [r[0] for r in rows]
    X = np.array([r[1] for r in rows], dtype=np.float32)
    clustering = DBSCAN(eps=0.35, min_samples=3, metric='cosine').fit(X)
    for fid, label in zip(ids, clustering.labels_):
        cur.execute("UPDATE faces SET cluster_id=%s WHERE id=%s", (int(label), fid))
    print(f"Clustered {len(ids)} wajah -> {len(set(clustering.labels_))} grup")

if __name__ == "__main__":
    print("face_worker siap. Panggil process_photo() untuk tiap foto di DB photos.")
