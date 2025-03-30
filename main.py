import os
import time
import requests
import logging
from flask import Flask, request
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from tqdm import tqdm

# Configurations
API_ID = 14050586  # Your Telegram API ID
API_HASH = "42a60d9c657b106370c79bb0a8ac560c"  # Your Telegram API Hash
BOT_TOKEN = "6956731651:AAE5v1XP5JcIQtsmjHiyemREawe1DQmgDpE"  # Your Telegram Bot Token
OWNER_ID = 5738579437  # Your Telegram ID
MONGO_URI = "mongodb+srv://Krishna:pss968048@cluster0.4rfuzro.mongodb.net/?retryWrites=true&w=majority"  # Your MongoDB URL
FLASK_PORT = 5000  # Change if needed
DUMP_CHANNEL = -1002565616015  # Dump channel ID

TERABOX_API = "https://teraboxdown.rishuapi.workers.dev/?url="  # TeraBox API URL

# Force Join Channels
FORCE_JOIN_CHANNELS = ["@Rishu_mood", "@Channel2", "@Channel3"]
FORCE_JOIN_BOT_TOKEN = "your_force_join_bot_token"  # Token for Force Join Bot

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client["TeraBoxBot"]
users_collection = db["users"]
premium_collection = db["premium"]
files_collection = db["files"]


# Flask Setup
app = Flask(__name__)

# Pyrogram Bot
bot = Client("TeraBoxBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Logging
logging.basicConfig(level=logging.INFO)

# Function to Check Force Join using Force Join Bot Token
def is_user_joined(user_id):
    for channel in FORCE_JOIN_CHANNELS:
        url = f"https://api.telegram.org/bot{FORCE_JOIN_BOT_TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}"
        response = requests.get(url).json()
        if not response.get("ok") or response["result"]["status"] not in ["member", "administrator", "creator"]:
            return False
    return True

# Function to reset daily limits
def reset_daily_limits():
    users_collection.update_many({}, {"$set": {"daily_count": 0}})

# Schedule reset at midnight
scheduler = BackgroundScheduler()
scheduler.add_job(reset_daily_limits, "cron", hour=0, minute=0)
scheduler.start()

# Function to check premium status
def is_premium(user_id):
    return premium_collection.find_one({"user_id": user_id}) is not None

# Function to update user download count
def update_download_count(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        users_collection.update_one({"user_id": user_id}, {"$inc": {"daily_count": 1}})
    else:
        users_collection.insert_one({"user_id": user_id, "daily_count": 1})

# Notify Owner About New User
async def notify_owner(user):
    total_users = users_collection.count_documents({})
    await bot.send_message(
        OWNER_ID,
        f"👤 **New User:** {user.mention} (@{user.username})\n📊 **Total Users:** {total_users}"
    )

# Start Message & File Sharing
@bot.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    args = message.command[1] if len(message.command) > 1 else None

    # Check Force Join
    if not is_user_joined(user_id):
        buttons = [[InlineKeyboardButton(f"🔹 Join {channel}", url=f"https://t.me/{channel[1:]}")] for channel in FORCE_JOIN_CHANNELS]
        buttons.append([InlineKeyboardButton("✅ Done! Check Again", callback_data="check_join")])
        return await message.reply_text(
            "⚠ **You must join all channels to use this bot!**\n\n📌 **Join the channels below:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # Register User in DB
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "daily_count": 0})
        await notify_owner(message.from_user)

    # Send Sticker & Progress Animation
    sticker = await message.reply_sticker("CAACAgUAAxkBAAEOL79n6KUaL5fqYoJI_e-fxCcYbU0wXQACCxsAAs5nQFQPvy-hVCAoTjYE")
    await asyncio.sleep(2)
    await sticker.delete()

    progress = [
        "[■□□□□□□□□□] 10%", "[■■□□□□□□□□] 20%", "[■■■□□□□□□□] 30%",
        "[■■■■□□□□□□] 40%", "[■■■■■□□□□□] 50%", "[■■■■■■□□□□] 60%",
        "[■■■■■■■□□□] 70%", "[■■■■■■■■□□] 80%", "[■■■■■■■■■□] 90%",
        "[■■■■■■■■■■] 100%"
    ]
    baby = await message.reply_text("[□□□□□□□□□□] 0%")
    for step in progress:
        await baby.edit_text(f"**{step}**")
        await asyncio.sleep(0.2)
    await baby.delete()

    # File Sharing Feature
    if args and args.startswith("file_"):
        file_id = args.split("_")[1]
        file_data = files_collection.find_one({"file_id": file_id})
        if not file_data:
            return await message.reply_text("❌ **File not found!**")

        file_type = file_data.get("type", "document")
        caption = f"📁 **{file_data['file_name']}**\n\n🔗 **Shared via TeraBox Bot**"
        buttons = [[InlineKeyboardButton("🔗 Share Again", url=f"https://t.me/{bot.me.username}?start=file_{file_id}")]]

        if file_type == "photo":
            await message.reply_photo(file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
        elif file_type == "video":
            await message.reply_video(file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await message.reply_document(file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Send Start Message
    await message.reply_text(
        f"👋 **Hello {message.from_user.mention}**\n\n"
        "🚀 **Welcome to TeraBox Downloader Bot!**\n\n"
        "📥 **Send a TeraBox link to get started.**\n"
        "🔹 **Normal Users:** 1 video/day\n"
        "🔹 **Premium Users:** 15 videos/day\n\n"
        "⚡ **Powered by** [RishuCoder](t.me/RishuApi)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates", url="https://t.me/Ur_Rishu_143"),
             InlineKeyboardButton("💬 Support", url="https://t.me/ur_support")]
        ])
    )


# Add Premium User
@bot.on_message(filters.command("addpremium") & filters.user(OWNER_ID))
async def add_premium(client, message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/addpremium user_id`")

    user_id = int(message.command[1])
    if is_premium(user_id):
        return await message.reply_text("User is already premium!")

    premium_collection.insert_one({"user_id": user_id})
    await message.reply_text(f"✅ **User {user_id} is now Premium!**")

# Remove Premium User
@bot.on_message(filters.command("delpremium") & filters.user(OWNER_ID))
async def remove_premium(client, message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/delpremium user_id`")

    user_id = int(message.command[1])
    if not is_premium(user_id):
        return await message.reply_text("User is not premium!")

    premium_collection.delete_one({"user_id": user_id})
    await message.reply_text(f"❌ **User {user_id} is removed from Premium!**")


# Fetch File Details & Send Button
@bot.on_message(filters.text & filters.private)
async def fetch_file_details(client, message):
    user_id = message.from_user.id
    user = users_collection.find_one({"user_id": user_id}) or {"daily_count": 0}
    max_limit = 15 if is_premium(user_id) else 1

    if user["daily_count"] >= max_limit:
        return await message.reply_text("❌ **Daily limit reached!**")

    url = message.text.strip()

    # Fetch File Details from API
    await message.reply_text("🔄 **Fetching file details...**")
    response = requests.get(TERABOX_API + url).json()

    if "file_name" not in response:
        return await message.reply_text("❌ **Invalid or expired link!**")

    file_name = response["file_name"]
    file_size = response["size"]
    file_link = response["link"]
    thumb_url = response["thumb"]

    # Send File Details with Spoiler Thumbnail & Download Button
    await message.reply_photo(
        thumb_url, has_spoiler=True,
        caption=f"📂 **File Name:** `{file_name}`\n📏 **Size:** `{file_size}`\n\nClick below to download! 👇",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📥 Download", callback_data=f"download|{file_link}|{file_name}")]]
        )
    )

# Handle Download Button Click
@bot.on_callback_query(filters.regex("^download\|"))
async def handle_download(client, query):
    data = query.data.split("|")
    file_link = data[1]
    file_name = data[2]

    await query.message.reply_text(f"⬇ **Downloading `{file_name}`...**")
    file_path = f"downloads/{file_name}"

    with requests.get(file_link, stream=True) as r, open(file_path, "wb") as file, tqdm(
        desc="Downloading", unit="MB", total=int(r.headers.get("content-length", 0)) / (1024 * 1024)
    ) as pbar:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)
                pbar.update(len(chunk) / (1024 * 1024))

    await query.message.reply_text(f"✅ **Download Complete! Uploading to Telegram...**")

    # Upload to Dump Channel
    sent_msg = await bot.send_document(
        chat_id=DUMP_CHANNEL,
        document=file_path,
        caption=f"📂 **{file_name}**\n📏 **Size:** {r.headers.get('content-length', 'Unknown')}"
    )

    # Generate Shareable Link
    file_id = sent_msg.document.file_id
    share_link = f"https://t.me/{bot.me.username}?start=file_{file_id}"

    # Check File Type (Video, Photo, Document)
    if file_name.lower().endswith((".mp4", ".mkv", ".avi")):
        await query.message.reply_video(
            video=file_path,
            caption=f"✅ **Your File is Ready!**\n\n📂 **{file_name}**\n🔗 **[Share Again]({share_link})**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share File", url=share_link)]])
        )
    elif file_name.lower().endswith((".jpg", ".jpeg", ".png")):
        await query.message.reply_photo(
            photo=file_path,
            caption=f"✅ **Your File is Ready!**\n\n📂 **{file_name}**\n🔗 **[Share Again]({share_link})**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share File", url=share_link)]])
        )
    else:
        await query.message.reply_document(
            document=file_path,
            caption=f"✅ **Your File is Ready!**\n\n📂 **{file_name}**\n🔗 **[Share Again]({share_link})**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share File", url=share_link)]])
        )

    os.remove(file_path)
    update_download_count(query.from_user.id)

# Broadcast System
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast(client, message):
    text = message.text.split(" ", 1)[1] if len(message.text.split()) > 1 else None
    if not text:
        return await message.reply_text("❌ **Usage:** `/broadcast Your message here`")

    for user in users_collection.find():
        try:
            await bot.send_message(user["user_id"], text)
        except Exception:
            continue

    await message.reply_text("✅ **Broadcast Sent!**")

# Flask Webhook
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    bot.process_update(update)
    return "OK", 200

if __name__ == "__main__":
    bot.start()
    app.run(host="0.0.0.0", port=FLASK_PORT)
