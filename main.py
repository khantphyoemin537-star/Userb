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
STRING_SESSION = "1BVtsOIMBu6aMRXlnbKtRUDENsZ2bEpBRNkCkyDz6i1oo6WTMItIV7_rxmIr1jumIIMJBqA6imApY27eMSst8osic_msGyfD3LrdflBOHWnipwcTJUQzKqnDiJZCfW4T3LOZYKdtv5pfnft3ZIbgH6hZxbqfzxzRi94Ktz5k6ns-_6x5KeVmJyID8MBKEEUlUsEwRb2g0qz08x6kKF_0YcH5GrbLSqL9FgGKSL1Wd9gi9bezX1DsVdz4LhfqbXh4M0kcYQjFt97QEO_tpFJZ1krcjtL4l2-FCyvIlFy8U28xQzfqgtBOanK8IFE01viVERSW_KIi20psHe5TAVrQpNGYARo-VclI="
TARGET_CHAT_ID = -1003580630981

# MongoDB
MONGO_URI = "mongodb://khantphyoemin537_db_user:9VRKiaeZkz7rJdpz@cluster0-shard-00-00.w6tgi8j.mongodb.net:27017,cluster0-shard-00-01.w6tgi8j.mongodb.net:27017,cluster0-shard-00-02.w6tgi8j.mongodb.net:27017/?ssl=true&replicaSet=atlas-w6tgi8j-shard-0&authSource=admin&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"

db_client = MongoClient(MONGO_URI)
db = db_client["SpySystem_DB"]
blacklist_db = db["permanent_blacklist"]

app = Flask(__name__)
@app.route("/")
def home(): return "🦇 Bot Terminator is Online"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

async def main():
    await client.connect()
    me = await client.get_me()
    print(f"✅ Logged in as: {me.first_name}")

    # ၁။ /del နဲ့ Blacklist သွင်းတဲ့အပိုင်း
    @client.on(events.NewMessage(chats=TARGET_CHAT_ID, pattern=r"(?i)^/del$"))
    async def set_blacklist(event):
        if not event.is_reply: return
        
        reply_msg = await event.get_reply_message()
        reply_sender = await reply_msg.get_sender()

        # Reply ထောက်ခံရသူက Bot ဖြစ်ရမယ်
        if reply_sender and getattr(reply_sender, 'bot', False):
            bot_id = reply_sender.id
            
            # DB ထဲမှာ သိမ်းမယ်
            blacklist_db.update_one(
                {"chat_id": TARGET_CHAT_ID, "bot_id": bot_id},
                {"$set": {"bot_name": reply_sender.first_name}},
                upsert=True
            )

            # Bot စာကို ၁ စက္ကန့်အတွင်း ဖျက်မယ်
            await asyncio.sleep(1)
            await reply_msg.delete()

            # Mention နဲ့ Animation ပြမယ့်အပိုင်း
            bot_mention = f"[@{reply_sender.username}](tg://user?id={bot_id})" if reply_sender.username else reply_sender.first_name
            group_info = await client.get_entity(TARGET_CHAT_ID)
            
            base_text = f"💀 {bot_mention} ကို Blacklist သွင်းလိုက်ပြီ။\n{group_info.title} မှာ သူပို့သမျှ အမြဲပျက်ပါတော့မယ်။"
            anim_msg = await event.respond(f"{base_text}\n\n⏳ 5")

            for i in range(4, 0, -1):
                await asyncio.sleep(1)
                await anim_msg.edit(f"{base_text}\n\n⏳ {i}")

            await asyncio.sleep(1)
            await anim_msg.delete()
            await event.delete() # /del စာသားကိုပါ ဖျက်မယ်

    # ၂။ Blacklist မိထားတဲ့ Bot စာပို့တိုင်း အမြဲလိုက်ဖျက်မယ့်အပိုင်း
    @client.on(events.NewMessage(chats=TARGET_CHAT_ID))
    async def auto_purge(event):
        if event.sender and getattr(event.sender, 'bot', False):
            # DB မှာ စစ်မယ်
            is_blacklisted = blacklist_db.find_one({
                "chat_id": TARGET_CHAT_ID,
                "bot_id": event.sender_id
            })

            if is_blacklisted:
                await asyncio.sleep(1) # ၁ စက္ကန့်အတွင်း ဖျက်မယ်
                try:
                    await event.delete()
                    print(f"🗑 Silently purged blacklisted bot: {event.sender_id}")
                except:
                    pass

    await client.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
