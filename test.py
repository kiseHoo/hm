import asyncio import os import time import requests import logging from flask import Flask, request from pymongo import MongoClient from apscheduler.schedulers.background import BackgroundScheduler from pyrogram import Client, filters, idle from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton from tqdm import tqdm from threading import Thread

Configurations

API_ID = 14050586  # Your Telegram API ID API_HASH = "42a60d9c657b106370c79bb0a8ac560c"  # Your Telegram API Hash BOT_TOKEN = "6956731651:AAE5v1XP5JcIQtsmjHiyemREawe1DQmgDpE"  # Your Telegram Bot Token OWNER_ID = 5738579437  # Your Telegram ID MONGO_URI = "mongodb+srv://Krishna:pss968048@cluster0.4rfuzro.mongodb.net/?retryWrites=true&w=majority"  # Your MongoDB URL FLASK_PORT = 5000  # Change if needed DUMP_CHANNEL = -1002565616015  # Dump channel ID

TERABOX_API = "https://teraboxdown.rishuapi.workers.dev/?url="  # TeraBox API URL

MongoDB Setup

client = MongoClient(MONGO_URI) db = client["TeraBoxBot"] users_collection = db["users"] premium_collection = db["premium"] files_collection = db["files"]

Flask Setup

app = Flask(name)

Pyrogram Bot

bot = Client("TeraBoxBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

Logging

logging.basicConfig(level=logging.INFO)

Function to reset daily limits

def reset_daily_limits(): users_collection.update_many({}, {"$set": {"daily_count": 0}})

Schedule reset at midnight

scheduler = BackgroundScheduler() scheduler.add_job(reset_daily_limits, "cron", hour=0, minute=0) scheduler.start()

Start Message & File Sharing

@bot.on_message(filters.command("start")) async def start(client, message): await message.reply_text("✅ Bot is Running!")

Flask Webhook

@app.route("/", methods=["POST"]) def webhook(): update = request.get_json() if not update: return "Invalid Data", 400  # Bad Request

bot.process_update(update)
return "OK", 200

Running Flask & Bot together

if name == "main": Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": FLASK_PORT, "threaded": True}).start() bot.start() print("✅ Bot started successfully!") idle() bot.stop()

