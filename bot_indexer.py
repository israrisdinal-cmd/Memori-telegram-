# bot_indexer.py - Telegram Photo Memories Bot
# Metadata-only, foto tetap di Telegram
# pip install python-telegram-bot psycopg2-binary fastapi uvicorn
#
# Env:
# BOT_TOKEN=...
# DATABASE_URL=postgresql://...
# ARCHIVE_CHANNEL_ID=-100...
#
import os, asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import psycopg2

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", "0"))

conn = psycopg2.connect(DB_URL)
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

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg or not msg.photo: return
    p = msg.photo[-1]
    file_id = p.file_id
    file_unique_id = p.file_unique_id
    taken_at = msg.date
    caption = msg.caption or ""
    chat_id = msg.chat.id
    message_id = msg.message_id
    try:
        cur.execute("""
          INSERT INTO photos (file_id, file_unique_id, message_id, chat_id, taken_at, caption)
          VALUES (%s,%s,%s,%s,%s,%s)
          ON CONFLICT (file_id) DO NOTHING
        """, (file_id, file_unique_id, message_id, chat_id, taken_at, caption))
        print(f"indexed {message_id} {taken_at}")
    except Exception as e:
        print("db err", e)

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot indexer jalan. Add bot ke channel Arsip sebagai admin Read Messages.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
