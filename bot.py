import logging
import re
import os
import httpx
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

active_otp_tasks = {}

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

ALLOWED_COUNTRIES = {
    "232": {"name": "Sierra Leone", "flag": "🇸🇱"},
    "224": {"name": "Guinea", "flag": "🇬🇳"},
    "225": {"name": "Ivory Coast", "flag": "🇨🇮"},
    "261": {"name": "Madagascar", "flag": "🇲🇬"},
    "229": {"name": "Benin", "flag": "🇧🇯"},
}

async def call_website_api_async(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload or {}, headers=headers)
            
            if r.status_code != 200:
                logger.warning(f"API {endpoint} failed: {r.status_code}")
                return None
            return r.json()
    except Exception as e:
        logger.error(f"API call error: {e}")
        return None


async def auto_refresh_ranges():
    while True:
        try:
            await call_website_api_async("liveaccess", method="GET")
        except Exception as e:
            logger.error(f"Auto refresh error: {e}")
        await asyncio.sleep(60)


async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except Exception as e:
        logger.warning(f"Subscription check failed: {e}")
        return False  # বা True করে টেস্ট করতে পারেন


async def start(update: Update, context):
    user_id = update.effective_user.id
    logger.info(f"Start command from user {user_id}")
    
    if not await is_user_subscribed(context, user_id):
        kb = [
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify")]
        ]
        await update.message.reply_text(
            "বটটি ব্যবহার করতে প্রথমে আমাদের গ্রুপগুলোতে জয়েন করুন এবং নিচে ভেরিফাই বাটনে ক্লিক করুন।",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        await update.message.reply_text(
            "আপনি ভেরিফাইড ইউজার। নিচে থেকে সার্ভিস সিলেক্ট করুন।",
            reply_markup=main_keyboard
        )


async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    # ... (আপনার আগের কোডের বাকি অংশ রাখুন)


async def text_handler(update: Update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        return await start(update, context)
    
    text = update.message.text
    if "GET NUMBER" in text:
        await update.message.reply_text("দেশ সিলেক্ট করুন (এখনো আংশিক)")
    elif "2FA" in text:
        await update.message.reply_text("Maintenance Mode.")
    elif "LIVE OTP" in text:
        await update.message.reply_text("Join Channel:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📡 View Live", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]]))


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    asyncio.create_task(auto_refresh_ranges())

    logger.info("🤖 SUPER FIRE OTP Bot Started!")
    app.run_polling(drop_pending_updates=True)
