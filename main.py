import os
import asyncio
import dns.resolver
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pymongo import MongoClient
from flask import Flask
from threading import Thread

# Render DNS Fix
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '1.1.1.1']

# --- Configurations ---
API_ID = 38225985
API_HASH = "0b6330bc916f9e29d6bf302be079e9d6"
STRING_SESSION = "1BVtsOIMBu1ahaAgHtcx02XVWflkx0susCbNB78dAsmEJBxqg45kYlqxSOo-xXiTqI_3eBfKcf-gyI-G20sq6ra__fH0TBOhdn1vDJnLv-wKbssoHhVuu7j0cTzJYlYeW3-8oVoCdW5AliPIkOmKb18aBwOSVeMC2bKMruPO8y8DWlEpSjF1i04mpDjsEGUvpeWplPpS1w09CiqiLKuHkGQNVchQG8HUxz0fARXHRf6hFaSj55eLvmVud8q-mwFeyY3zz1Zd4lHaQ0tHzvGTEllE0VmV2LGHIwGQAoEj9MKQERT_okUZh03i5htEUfkYxXb9YEaPI3ATvN6-ivNAMelcpEQisVcc="

# MongoDB Standard URI (Render မှာ SRV ထက် ဒါက ပိုအလုပ်လုပ်တယ်)
MONGO_URI = "mongodb://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0-shard-00-00.w6tgi8j.mongodb.net:27017,cluster0-shard-00-01.w6tgi8j.mongodb.net:27017,cluster0-shard-00-02.w6tgi8j.mongodb.net:27017/?ssl=true&replicaSet=atlas-w6tgi8j-shard-0&authSource=admin&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

# Global list to store blacklisted IDs (DB မတက်လည်း အလုပ်လုပ်အောင်)
temp_blacklist = []

try:
    db_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = db_client["SpySystem_DB"]
    blacklist_db = db["permanent_blacklist_v4"]
    # စစချင်းမှာ DB ထဲက Bot တွေကို list ထဲ ထည့်ထားမယ်
    for bot in blacklist_db.find():
        temp_blacklist.append(bot['bot_id'])
    print("✅ MongoDB Connected & Syncing...")
except Exception as e:
    print(f"❌ DB Error: {e} (Using temporary memory instead)")

app = Flask(__name__)
@app.route("/")
def home(): return "🦇 Dexter's Absolute Terminator Live"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

async def show_animation(event, bot_sender, group_title):
    bot_mention = f"[@{bot_sender.username}](tg://user?id={bot_sender.id})" if bot_sender.username else bot_sender.first_name
    base_text = f"🔥 **Terminator Alert!**\n\n{bot_mention} ကို {group_title} ကနေ ရှင်းထုတ်လိုက်ပြီ။\nငါ့စာလည်း 5 sec ဆို ပျောက်မယ်။"
    anim_msg = await event.respond(f"{base_text}\n\n⏳ 5")
    for i in range(4, 0, -1):
        await asyncio.sleep(1)
        try: await anim_msg.edit(f"{base_text}\n\n⏳ {i}")
        except: pass
    await asyncio.sleep(1)
    await anim_msg.delete()

async def main():
    await client.connect()
    print("✅ Client connected!")

    # ၁။ /dexterdel - Bot ကို Blacklist သွင်းမယ်
    @client.on(events.NewMessage(pattern=r"(?i)^/dexterdel$"))
    async def manual_add(event):
        if not event.is_reply: return
        reply_msg = await event.get_reply_message()
        reply_sender = await reply_msg.get_sender()

        if reply_sender and getattr(reply_sender, 'bot', False):
            bot_id = reply_sender.id
            if bot_id not in temp_blacklist:
                temp_blacklist.append(bot_id)
                # DB မှာ သိမ်းမယ်
                try:
                    blacklist_db.update_one(
                        {"bot_id": bot_id},
                        {"$set": {"bot_name": reply_sender.first_name}},
                        upsert=True
                    )
                except: pass

            await asyncio.sleep(0.5)
            await reply_msg.delete()
            await event.delete()
            chat = await event.get_chat()
            await show_animation(event, reply_sender, chat.title)

    # ၂။ Blacklist မိထားတဲ့ Bot ကို အမြဲလိုက်ဖျက်မယ်
    @client.on(events.NewMessage)
    async def auto_purge(event):
        if event.sender_id in temp_blacklist:
            await asyncio.sleep(0.5)
            try:
                await event.delete()
                chat = await event.get_chat()
                await show_animation(event, event.sender, chat.title)
            except: pass

    await client.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    client.loop.run_until_complete(main())
