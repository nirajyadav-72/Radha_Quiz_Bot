import os
import sqlite3
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UserIsBlocked

# .env file load karein
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

# 💾 DATABASE SETUP (Yeh ek 'users.db' naam ki file bana dega)
DB_FILE = "users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Users table banayein agar nahi bani hai toh
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def remove_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Database ko initialize karein
init_db()

# Bot client initialize karein
app = Client("quiz_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start Command (User ko DB me save karega)
@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    add_user(user_id)  # DB me user ID save ho gayi
    await message.reply_text("Welcome to the Quiz Bot!")

# Broadcast Command
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("🔊 Use: /broadcast [Aapka Message]")
        return
    
    broadcast_message = message.text.split(None, 1)[1]
    
    status_msg = await message.reply_text("⏳ Broadcast shuru ho raha hai...")
    
    # Database se saare users ko nikaalein
    all_users = get_all_users()
    
    success = 0
    failed = 0

    for u_id in all_users:
        try:
            await client.send_message(chat_id=u_id, text=broadcast_message)
            success += 1
        except (UserIsBlocked, PeerIdInvalid):
            # Agar user ne bot block kiya toh DB se delete karein
            remove_user(u_id)
            failed += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"📢 **Broadcast Complete!**\n\n"
        f"✅ Safal: {success}\n"
        f"❌ Asafal: {failed}"
    )

# Uncertified Users Alert
@app.on_message(filters.command("broadcast") & ~filters.user(OWNER_ID))
async def unauthorized_broadcast(client: Client, message: Message):
    await message.reply_text("❌ Aapke paas is command ka access nahi hai!")

if __name__ == "__main__":
    app.run()
