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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"
active_otp_tasks = {}
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

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

dynamic_countries = ALLOWED_COUNTRIES.copy()

def get_country_details(number_str):
    clean_num = re.sub(r'\D', '', str(number_str))
    prefix = clean_num[:3]
    return dynamic_countries.get(prefix)

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
                return None
            return r.json()
    except Exception as e:
        logging.error(f"API call error: {e}")
        return None

async def auto_refresh_ranges():
    while True:
        await call_website_api_async("liveaccess", method="GET")
        await asyncio.sleep(60)

async def start(update: Update, context):
    await update.message.reply_text("বট চালু আছে।\nGET NUMBER চাপুন।", reply_markup=main_keyboard)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Feature under development.")

async def show_countries(msg):
    kb = []
    for prefix, country in dynamic_countries.items():
        kb.append([InlineKeyboardButton(f"{country['flag']} {country['name']}", callback_data=f"range_any_{prefix}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    await msg.reply_text("**দেশ সিলেক্ট করুন:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

async def text_handler(update: Update, context):
    text = update.message.text
    if "GET NUMBER" in text:
        await show_countries(update.message)
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

    logging.info("🤖 SUPER FIRE OTP Bot Started!")
    app.run_polling(drop_pending_updates=True)
