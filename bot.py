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
            
            return r.json() if r.status_code == 200 else None
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None


async def auto_refresh_ranges():
    while True:
        await call_website_api_async("liveaccess", method="GET")
        await asyncio.sleep(60)


async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(UPDATE_CHANNEL, user_id)
        m2 = await context.bot.get_chat_member(OTP_CHANNEL, user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except:
        return False


async def check_otp(context, chat_id, number):
    full_number = re.sub(r'\D', '', str(number))
    seen_otps = set()

    try:
        for attempt in range(900):
            await asyncio.sleep(2)
            res = await call_website_api_async("success-otp-info", method="GET")
            
            if res and "data" in res:
                for item in res["data"].get("otps", []):
                    item_num = re.sub(r'\D', '', str(item.get("number", "")))
                    if item_num == full_number or item_num.endswith(full_number[-8:]):
                        otp = item.get("otp") or item.get("code") or item.get("sms")
                        if otp and otp not in seen_otps:
                            seen_otps.add(otp)
                            country = ALLOWED_COUNTRIES.get(full_number[:3], {"flag": "🌍", "name": "Unknown"})
                            
                            text = f"✅ **OTP RECEIVED!**\nNumber: +{number}\nCode: `{otp}`"
                            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
                            return
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Check OTP Error: {e}")


async def start(update: Update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await update.message.reply_text("প্রথমে চ্যানেলে জয়েন করুন।")
    else:
        await update.message.reply_text("স্বাগতম!", reply_markup=main_keyboard)


async def text_handler(update: Update, context):
    if "GET NUMBER" in update.message.text:
        await update.message.reply_text("দেশ সিলেক্ট করুন (এখনো আংশিক)")
    elif "LIVE OTP" in update.message.text:
        await update.message.reply_text("Live OTP চ্যানেল দেখুন।")


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    asyncio.create_task(auto_refresh_ranges())

    logger.info("🤖 Bot Started Successfully!")
    app.run_polling(drop_pending_updates=True)
