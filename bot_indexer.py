import os, time
import psycopg2
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from telegram.request import HTTPXRequest

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

print("BOT_TOKEN set:", bool(BOT_TOKEN))
print("DATABASE_URL set:", bool(DATABASE_URL))

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS photos (
  file_id TEXT PRIMARY KEY,
  file_unique_id TEXT UNIQUE,
  message_id BIGINT,
  chat_id BIGINT,
  taken_at TIMESTAMPTZ,
  caption TEXT
);
CREATE INDEX IF NOT EXISTS photos_date_idx ON photos(taken_at);
""")

async def handle_photo(update: Update, context):
    msg = update.channel_post or update.message
    if not msg or not msg.photo:
        return
    p = msg.photo[-1]
    try:
        cur.execute("""
            INSERT INTO photos (file_id, file_unique_id, message_id, chat_id, taken_at, caption)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_id) DO NOTHING
        """, (p.file_id, p.file_unique_id, msg.message_id, msg.chat.id, msg.date, msg.caption or ""))
        print(f"indexed {msg.message_id}")
    except Exception as e:
        print("db err", e)

def run():
    request = HTTPXRequest(connect_timeout=60, read_timeout=60, write_timeout=60, pool_timeout=60)
    app = Application.builder().token(BOT_TOKEN).request(request).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot indexer jalan. Add bot ke channel")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print("crash, retry in 15s:", e)
            time.sleep(15)
