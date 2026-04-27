import os
import asyncio
import dns.resolver
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pymongo import MongoClient
from flask import Flask
from threading import Thread

# Termux/Render DNS Fix
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

# --- Configurations ---
API_ID = 38225985
API_HASH = "0b6330bc916f9e29d6bf302be079e9d6"
OWNER_ID = 6015356597 # သခင်လေးရဲ့ ID

MONGO_URI = "mongodb://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0-shard-00-00.w6tgi8j.mongodb.net:27017,cluster0-shard-00-01.w6tgi8j.mongodb.net:27017,cluster0-shard-00-02.w6tgi8j.mongodb.net:27017/?ssl=true&replicaSet=atlas-w6tgi8j-shard-0&authSource=admin&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

db_client = MongoClient(MONGO_URI)
db = db_client["SpySystem_DB"]
sessions_db = db["active_strings"]
blacklist_db = db["blacklisted_bots"]

app = Flask(__name__)
@app.route("/")
def home(): return "🦇 Dexter Bot Cleaner Online"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def start_cleaner(session_str):
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        me = await client.get_me()
        uid = me.id
        print(f"✅ Started for: {me.first_name}")

        @client.on(events.NewMessage(pattern=r"(?i)^/deleteit$"))
        async def add_to_blacklist(event):
            # ပိုင်ရှင်ကိုယ်တိုင် (သို့) သခင်လေး ခိုင်းမှ အလုပ်လုပ်မယ်
            if event.sender_id == uid or event.sender_id == OWNER_ID:
                if not event.is_group or not event.is_reply: return
                
                reply_msg = await event.get_reply_message()
                reply_sender = await reply_msg.get_sender()

                if reply_sender and getattr(reply_sender, 'bot', False):
                    bot_id = reply_sender.id
                    chat_id = event.chat_id

                    blacklist_db.update_one(
                        {"chat_id": chat_id, "bot_id": bot_id},
                        {"$set": {"bot_name": reply_sender.first_name}},
                        upsert=True
                    )

                    await asyncio.sleep(2)
                    await reply_msg.delete()

                    base_text = f"🚫 **@{reply_sender.username}** ကို Blacklist သွင်းလိုက်ပြီ။\nငါ့စာဟာလည်း 5 sec အတွင်း ပျက်ပါမယ်။"
                    anim_msg = await event.respond(f"{base_text}\n\n⏳ 5")

                    for i in range(4, 0, -1):
                        await asyncio.sleep(1)
                        await anim_msg.edit(f"{base_text}\n\n⏳ {i}")

                    await asyncio.sleep(1)
                    await anim_msg.delete()
                    await event.delete()

        @client.on(events.NewMessage)
        async def auto_clean(event):
            if event.is_group and event.sender and getattr(event.sender, 'bot', False):
                is_blacklisted = blacklist_db.find_one({"chat_id": event.chat_id, "bot_id": event.sender_id})
                if is_blacklisted:
                    await asyncio.sleep(2)
                    try: await event.delete()
                    except: pass

        await client.run_until_disconnected()
    except Exception as e: print(f"Error: {e}")

async def init_system():
    for s in sessions_db.find(): asyncio.create_task(start_cleaner(s["session"]))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.create_task(init_system())
    loop.run_forever()
