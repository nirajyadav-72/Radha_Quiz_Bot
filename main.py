import os
import sqlite3
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UserIsBlocked, ChatWriteForbidden

# .env file load karein
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

DB_FILE = "quiz_bot.db"

# 💾 DATABASE FUNCTIONS
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def add_group(group_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO groups (group_id) VALUES (?)", (group_id,))
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()] # row[0] se clean integer list milegi
    cursor.execute("SELECT group_id FROM groups")
    groups = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users, groups

def remove_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def remove_group(group_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
    conn.commit()
    conn.close()

# Database initialize karein
init_db()

app = Client("quiz_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 📥 AUTOMATIC TRACKING
@app.on_message(filters.private & filters.command("start"))
async def start_private(client: Client, message: Message):
    add_user(message.from_user.id)
    await message.reply_text("👋 Welcome to the Quiz Bot in Private Chat!")

@app.on_message(filters.group)
async def track_groups(client: Client, message: Message):
    add_group(message.chat.id)
    if message.text and message.text.startswith("/start"):
        await message.reply_text("👋 Quiz Bot ab is group me active hai!")

# 📢 COMBINED BROADCAST COMMAND
@app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("🔊 **Use:** `/broadcast [Aapka Message]`")
        return
    
    # ✅ FIX: Yahan [1] lagane se ab list nahi, sirf text extract hoga
    broadcast_message = message.text.split(None, 1)[1]
    status_msg = await message.reply_text("⏳ **Broadcast shuru ho raha hai...**")
    
    all_users, all_groups = get_all_data()
    u_success, u_failed = 0, 0
    g_success, g_failed = 0, 0

    # 1. Personal Chats me bhejein
    for u_id in all_users:
        try:
            await client.send_message(chat_id=u_id, text=broadcast_message)
            u_success += 1
        except (UserIsBlocked, PeerIdInvalid):
            remove_user(u_id)
            u_failed += 1
        except Exception:
            u_failed += 1

    # 2. Groups me bhejein
    for g_id in all_groups:
        try:
            await client.send_message(chat_id=g_id, text=broadcast_message)
            g_success += 1
        except (ChatWriteForbidden, PeerIdInvalid):
            remove_group(g_id)
            g_failed += 1
        except Exception:
            g_failed += 1

    # Final Report
    await status_msg.edit_text(
        f"📢 **Broadcast Report Complete!**\n\n"
        f"👤 **Private Chats:**\n"
        f"✅ Safal: {u_success} | ❌ Asafal: {u_failed}\n\n"
        f"👥 **Groups:**\n"
        f"✅ Safal: {g_success} | ❌ Asafal: {g_failed}"
    )

@app.on_message(filters.command("broadcast") & ~filters.user(OWNER_ID))
async def unauthorized_broadcast(client: Client, message: Message):
    await message.reply_text("❌ Aapke paas is command ka access nahi hai!")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 TELEGRAM QUIZ BOT IS STARTING UP...")
    print("📂 Database Connection: SUCCESSFUL [quiz_bot.db]")
    print(f"👑 Bot Owner Configured: {OWNER_ID}")
    print("✅ BOT DEPLOYED SUCCESSFULLY! RUNNING NOW...")
    print("="*50 + "\n")
    
    app.run()
    
