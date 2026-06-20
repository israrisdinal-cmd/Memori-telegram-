# Memori Telegram - On this day + Face grouping
Foto tetap di Telegram, tidak pakai memori HP.

Komponen:
- bot_indexer.py : catat file_id, tanggal, caption dari channel Arsip
- api.py : FastAPI /onthisday dan /people untuk Mini App
- face_worker.py : extract wajah, clustering DBSCAN
- web/ : Mini App v2 HTML

Deploy HP-only (Railway):
1. Buat akun di railway.app, New Project > Deploy from GitHub / Upload
2. Set Variables:
   BOT_TOKEN=token_baru_dari_BotFather
   DATABASE_URL=postgresql dari Railway Postgres plugin
   ARCHIVE_CHANNEL_ID=-100...
3. Start Command bot: python bot_indexer.py
   Start Command api: uvicorn api:app --host 0.0.0.0 --port $PORT
   Jalankan sebagai 2 service terpisah.
4. Face worker jalan manual: python face_worker.py, lalu panggil process_photo() untuk backfill, lalu cluster_all()
5. Mini App: upload web/index.html ke Vercel / Cloudflare Pages, ganti API_BASE_URL di file ke URL Railway api kamu.

Keamanan:
- JANGAN pernah paste BOT_TOKEN / channel ID di chat.
- Selalu pakai env vars.
- Jika token bocor, revoke di @BotFather segera.
