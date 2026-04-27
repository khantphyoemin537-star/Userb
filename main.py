import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pymongo import MongoClient
from flask import Flask
from threading import Thread

# --- Configurations ---
API_ID = 38225985
API_HASH = "0b6330bc916f9e29d6bf302be079e9d6"

# MongoDB
MONGO_URI = "mongodb://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0-shard-00-00.w6tgi8j.mongodb.net:27017,cluster0-shard-00-01.w6tgi8j.mongodb.net:27017,cluster0-shard-00-02.w6tgi8j.mongodb.net:27017/?ssl=true&replicaSet=atlas-w6tgi8j-shard-0&authSource=admin&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

db_client = MongoClient(MONGO_URI)
db = db_client["SpySystem_DB"]
sessions_db = db["active_strings"]
blacklist_db = db["blacklisted_bots"] # Bot ID တွေကို သိမ်းမယ့်နေရာ

app = Flask(__name__)
@app.route("/")
def home(): return "🦇 Permanent Bot Cleaner Online"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# ==========================================
# 🛠 CORE LOGIC: BLACKLIST & AUTO-DELETE
# ==========================================

async def start_cleaner(session_str):
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        me = await client.get_me()
        uid = me.id

        # ၁။ Blacklist သတ်မှတ်ခြင်း နှင့် Animation ပြခြင်း
        @client.on(events.NewMessage(pattern=r"(?i)^/deleteit$"))
        async def add_to_blacklist(event):
            if event.sender_id != uid or not event.is_group or not event.is_reply:
                return

            reply_msg = await event.get_reply_message()
            reply_sender = await reply_msg.get_sender()

            if reply_sender and getattr(reply_sender, 'bot', False):
                bot_id = reply_sender.id
                chat_id = event.chat_id

                # DB ထဲမှာ Blacklist သွင်းမယ်
                blacklist_db.update_one(
                    {"chat_id": chat_id, "bot_id": bot_id},
                    {"$set": {"bot_name": reply_sender.first_name}},
                    upsert=True
                )

                # ၂ စက္ကန့်စောင့်ပြီး Bot ရဲ့ လက်ရှိစာကို ဖျက်မယ်
                await asyncio.sleep(2)
                await reply_msg.delete()

                # Animation စာသား
                base_text = f"🚫 **@{reply_sender.username if reply_sender.username else 'Bot'}** ကို Blacklist သွင်းလိုက်ပြီ။\nသူ့စာတွေကို အမြဲလိုက်ရှင်းပေးပါ့မယ်။\nငါ့ရဲ့စာဟာလည်း 5 sec ဆိုရင် ပျက်သွားပါလိမ့်မယ်"
                anim_msg = await event.respond(f"{base_text}\n\n⏳ 5")

                # Countdown Animation (5 to 1)
                for i in range(4, 0, -1):
                    await asyncio.sleep(1)
                    await anim_msg.edit(f"{base_text}\n\n⏳ {i}")

                await asyncio.sleep(1)
                await anim_msg.delete()
                await event.delete()

        # ၂။ Blacklist ထဲက Bot တွေ စာပို့လာတိုင်း အလိုအလျောက် ရှင်းထုတ်ခြင်း
        @client.on(events.NewMessage)
        async def auto_clean(event):
            if not event.is_group:
                return

            # စာပို့တဲ့သူက Bot ဟုတ်မဟုတ် အရင်စစ်မယ် (မြန်အောင်လို့)
            if event.sender and getattr(event.sender, 'bot', False):
                # ဒီ Chat ထဲမှာ ဒီ Bot ကို Blacklist လုပ်ထားသလား DB မှာ စစ်မယ်
                is_blacklisted = blacklist_db.find_one({
                    "chat_id": event.chat_id,
                    "bot_id": event.sender_id
                })

                if is_blacklisted:
                    await asyncio.sleep(2) # ၂ စက္ကန့် စောင့်မယ်
                    try:
                        await event.delete()
                        print(f"🗑 Auto-deleted blacklisted bot in {event.chat_id}")
                    except:
                        pass # Admin power မရှိရင် ကျော်မယ်

        await client.run_until_disconnected()
    except Exception as e:
        print(f"Client Error: {e}")

async def init_system():
    for s in sessions_db.find():
        asyncio.create_task(start_cleaner(s["session"]))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.create_task(init_system())
    loop.run_forever()
