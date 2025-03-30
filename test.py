import asyncio 
import os 
import time 
import requests 
import logging
from flask import Flask, request from pymongo import MongoClient from apscheduler.schedulers.background import BackgroundScheduler from pyrogram import Client, filters from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton from tqdm 
import tqdm

Configurations

API_ID = 14050586 API_HASH = "42a60d9c657b106370c79bb0a8ac560c" BOT_TOKEN = "YOUR_BOT_TOKEN" OWNER_ID = 5738579437 MONGO_URI = "YOUR_MONGO_URI" FLASK_PORT = 5000 DUMP_CHANNEL = -1002565616015 TERABOX_API = "https://teraboxdown.rishuapi.workers.dev/?url=" FORCE_JOIN_CHANNELS = ["@Rishu_mood", "@Rishucoder", "@RishuTutorial"] FORCE_JOIN_BOT_TOKEN = "YOUR_FORCE_JOIN_BOT_TOKEN"

MongoDB Setup

client = MongoClient(MONGO_URI) db = client["TeraBoxBot"] users_collection = db["users"] premium_collection = db["premium"] files_collection = db["files"]

Flask Setup

app = Flask(name)

Pyrogram Bot

bot = Client("TeraBoxBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

Logging

logging.basicConfig(level=logging.INFO)

Function to check Force Join

def is_user_joined(user_id): for channel in FORCE_JOIN_CHANNELS: url = f"https://api.telegram.org/bot{FORCE_JOIN_BOT_TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}" response = requests.get(url).json() if not response.get("ok") or response["result"]["status"] not in ["member", "administrator", "creator"]: return False return True

Function to reset daily limits

def reset_daily_limits(): users_collection.update_many({}, {"$set": {"daily_count": 0}})

Schedule reset at midnight

scheduler = BackgroundScheduler() scheduler.add_job(reset_daily_limits, "cron", hour=0, minute=0) scheduler.start()

Function to check premium status

def is_premium(user_id): return premium_collection.find_one({"user_id": user_id}) is not None

Function to update user download count

def update_download_count(user_id): user = users_collection.find_one({"user_id": user_id}) if user: users_collection.update_one({"user_id": user_id}, {"$inc": {"daily_count": 1}}) else: users_collection.insert_one({"user_id": user_id, "daily_count": 1}})

Notify Owner About New User

async def notify_owner(user): total_users = users_collection.count_documents({}) await bot.send_message( OWNER_ID, f"👤 New User: {user.mention} (@{user.username})\n📊 Total Users: {total_users}" )

Start Command

@bot.on_message(filters.command("start")) async def start(client, message): user_id = message.from_user.id if not is_user_joined(user_id): buttons = [[InlineKeyboardButton(f"🔹 Join {channel}", url=f"https://t.me/{channel[1:]}")] for channel in FORCE_JOIN_CHANNELS] buttons.append([InlineKeyboardButton("✅ Done! Check Again", callback_data="check_join")]) return await message.reply_text( "⚠ You must join all channels to use this bot!", reply_markup=InlineKeyboardMarkup(buttons) ) if not users_collection.find_one({"user_id": user_id}): users_collection.insert_one({"user_id": user_id, "daily_count": 0}) await notify_owner(message.from_user) await message.reply_text("🚀 Welcome to TeraBox Downloader Bot! Send a link to start.")

Fetch File Details

@bot.on_message(filters.text & filters.private) async def fetch_file_details(client, message): user_id = message.from_user.id if users_collection.find_one({"user_id": user_id}).get("daily_count", 0) >= (15 if is_premium(user_id) else 1): return await message.reply_text("❌ Daily limit reached!") url = message.text.strip() response = requests.get(TERABOX_API + url).json() if "file_name" not in response: return await message.reply_text("❌ Invalid or expired link!") file_name, file_size, thumb_url = response["file_name"], response["size"], response["thumb"] await message.reply_photo( thumb_url, has_spoiler=True, caption=f"📂 {file_name}\n📏 {file_size}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download", callback_data=f"download|{url}|{file_name}")]]) )

Handle Download

@bot.on_callback_query(filters.regex("^download\|")) async def handle_download(client, query): data = query.data.split("|") file_link, file_name = data[1], data[2] file_path = f"downloads/{file_name}" with requests.get(file_link, stream=True) as r, open(file_path, "wb") as file, tqdm( desc="Downloading", unit="MB", total=int(r.headers.get("content-length", 0)) / (1024 * 1024) ) as pbar: for chunk in r.iter_content(chunk_size=1024 * 1024): if chunk: file.write(chunk) pbar.update(len(chunk) / (1024 * 1024)) sent_msg = await bot.send_document(DUMP_CHANNEL, document=file_path, caption=f"📂 {file_name}") os.remove(file_path) update_download_count(query.from_user.id) await query.message.reply_text(f"✅ Your File is Ready! \n📂 {file_name}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share File", url=f"https://t.me/{bot.me.username}?start=file_{sent_msg.document.file_id}")]]))

Broadcast

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID)) async def broadcast(client, message): text = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None if not text: return await message.reply_text("❌ Usage: /broadcast Your message here") for user in users_collection.find(): try: await bot.send_message(user["user_id"], text) except Exception: continue await message.reply_text("✅ Broadcast Sent!")

Flask Webhook

@app.route("/", methods=["POST"]) def webhook(): update = request.get_json() if update: bot.process_update(update) return "OK", 200

if name == "main": bot.start() app.run(host="0.0.0.0", port=FLASK_PORT, threaded=True)

lask Webhook

@app.route("/", methods=["POST"]) def webhook(): update = request.get_json() if not update: return "Invalid Data", 400  # Bad Request

bot.process_update(update)
return "OK", 200

Running Flask & Bot together

if name == "main": Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": FLASK_PORT, "threaded": True}).start() bot.start() print("✅ Bot started successfully!") idle() bot.stop()

