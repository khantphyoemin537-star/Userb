import os
import asyncio
import dns.resolver
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from pymongo import MongoClient
from flask import Flask
from threading import Thread

# DNS Fix
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']

# --- Configurations ---
API_ID = 38225985
API_HASH = "0b6330bc916f9e29d6bf302be079e9d6"
STRING_SESSION = "1BVtsOIMBuzruZV8QK0TMH8XjDKaLELaYGzzqeYkl_M9aZHj1Bi205ziFfa-pg3Dpm_64lG5FjAyDqjzORsaiRb11aDuQFYQm12irF-hAZZy-nmFEavqwjtjp06yjHMm0gqqc0atTWT0CZJ-XW3PJ4SAIcn4mh74esn2A6G7us-hixBEGYbZHyY4Q9CIrJ5dHsfAF56coU6zeW1xBoj26vk12Q9MTxJl9TRSoDT9ZpFbx1DLHBl-P2Yr8L0t93CcdWRnWCzeA9QkN6uCxVnwXqTuXq22H9-7vtTNi1q12ntmlBa8GiRH3jgtOIwniWDuW6nqYL9uCBK-4RqL60cOHwvv-0PkAfc0="
TARGET_CHAT_ID = -1003580630981 

# MongoDB
MONGO_URI = "mongodb://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0-shard-00-00.w6tgi8j.mongodb.net:27017,cluster0-shard-00-01.w6tgi8j.mongodb.net:27017,cluster0-shard-00-02.w6tgi8j.mongodb.net:27017/?ssl=true&replicaSet=atlas-w6tgi8j-shard-0&authSource=admin&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

db_client = MongoClient(MONGO_URI)
db = db_client["SpySystem_DB"]
blacklist_db = db["permanent_blacklist_v2"]

app = Flask(__name__)
@app.route("/")
def home(): return "🦇 Full Animation Terminator is Online"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

async def show_animation(event, bot_sender, group_title):
    """Animation နဲ့ Mention ပြသပေးမယ့် function"""
    bot_id = bot_sender.id
    bot_name = bot_sender.first_name
    bot_mention = f"[@{bot_sender.username}](tg://user?id={bot_id})" if bot_sender.username else bot_name
    
    base_text = f"🔥 **Terminator Alert!**\n\n{bot_mention} ရဲ့ စာကို {group_title} ကနေ ရှင်းထုတ်လိုက်ပြီ။\nငါ့စာလည်း 5 sec ဆို ပျောက်မယ်။"
    
    # Noti Message ကို Reply အနေနဲ့ ပို့မယ်
    anim_msg = await event.respond(f"{base_text}\n\n⏳ 5")
    
    for i in range(4, 0, -1):
        await asyncio.sleep(1)
        await anim_msg.edit(f"{base_text}\n\n⏳ {i}")
        
    await asyncio.sleep(1)
    await anim_msg.delete()

async def main():
    await client.connect()
    group_info = await client.get_entity(TARGET_CHAT_ID)
    group_title = group_info.title
    print(f"✅ Monitoring Group: {group_title}")

    # ၁။ /delbot နဲ့ အသစ်သွင်းတဲ့အပိုင်း
    @client.on(events.NewMessage(chats=TARGET_CHAT_ID, pattern=r"(?i)^/delbot$"))
    async def manual_add(event):
        if not event.is_reply: return
        reply_msg = await event.get_reply_message()
        reply_sender = await reply_msg.get_sender()

        if reply_sender and getattr(reply_sender, 'bot', False):
            blacklist_db.update_one(
                {"chat_id": TARGET_CHAT_ID, "bot_id": reply_sender.id},
                {"$set": {"bot_name": reply_sender.first_name}},
                upsert=True
            )
            await asyncio.sleep(1)
            await reply_msg.delete() # Bot စာကို အရင်ဖျက်
            await event.delete() # /delbot command ကိုဖျက်
            await show_animation(event, reply_sender, group_title) # Animation ပြ

    # ၂။ Blacklist မိထားတဲ့ Bot စာပို့ရင် အမြဲတမ်း Animation နဲ့ လိုက်ဖျက်မယ့်အပိုင်း
    @client.on(events.NewMessage(chats=TARGET_CHAT_ID))
    async def auto_purge_with_anim(event):
        if event.sender and getattr(event.sender, 'bot', False):
            is_blacklisted = blacklist_db.find_one({
                "chat_id": TARGET_CHAT_ID,
                "bot_id": event.sender_id
            })

            if is_blacklisted:
                await asyncio.sleep(1)
                try:
                    await event.delete() # Bot စာကို ချက်ချင်းဖျက်
                    # အပိုင်း ၂ အတွက်လည်း Animation ထည့်သွင်းခြင်း
                    await show_animation(event, event.sender, group_title)
                except Exception as e:
                    print(f"Purge Error: {e}")

    await client.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
