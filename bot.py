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

if not TOKEN or not API_KEY:
    raise ValueError("BOT_TOKEN বা SMS_API_KEY .env-এ নেই!")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_USERNAME = "SUPER_FIRE_OTP_BOT"
active_otp_tasks = {}
live_ranges = {}

COUNTRY_INFO = {
    "sl": {"flag": "🇸🇱", "name": "Sierra Leone"},
    "gn": {"flag": "🇬🇳", "name": "Guinea"},
    "ci": {"flag": "🇨🇮", "name": "Ivory Coast"},
    "mg": {"flag": "🇲🇬", "name": "Madagascar"},
    "bj": {"flag": "🇧🇯", "name": "Benin"},
}

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

async def call_api(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=12.0) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload or {}, headers=headers)
            return r.json() if r.status_code == 200 else None
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

async def fetch_live_ranges():
    global live_ranges
    while True:
        res = await call_api("liveaccess", "GET")
        if res:
            live_ranges = {}
            services = res.get("services") or res.get("data") or []
            for s in services if isinstance(services, list) else []:
                sid = str(s.get("sid", "")).lower().strip()
                if sid:
                    live_ranges[sid] = s.get("ranges", [])
            logger.info(f"Ranges Loaded: {len(live_ranges)}")
        await asyncio.sleep(20)

def get_country_keyboard():
    if not live_ranges:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh Ranges", callback_data="refresh")]])
    
    buttons = []
    for sid, ranges in live_ranges.items():
        if not ranges:
            continue
        key = sid.split("_")[0] if "_" in sid else sid[:2]
        if key in COUNTRY_INFO:
            info = COUNTRY_INFO[key]
            buttons.append([InlineKeyboardButton(f"{info['flag']} {info['name']}", callback_data=f"country_{key}_{sid}")])
    
    return InlineKeyboardMarkup(buttons) if buttons else InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh Ranges", callback_data="refresh")]])

async def start(update: Update, context):
    await update.message.reply_text("✅ স্বাগতম!", reply_markup=main_keyboard)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "refresh":
        await fetch_live_ranges()
        await query.message.edit_text("✅ Ranges Updated!\nআবার GET NUMBER চাপুন।")
        return

    if query.data.startswith("country_"):
        _, country_key, service_id = query.data.split("_", 2) if "_" in query.data else (None, country_key, country_key)
        status = await query.message.edit_text("⚡ Allocating number...")
        res = await call_api("getnum", "POST", {"range": "1", "service": service_id})
        if res and res.get("meta", {}).get("status") == "ok":
            num = res.get("data", {}).get("full_number") or res.get("data", {}).get("number")
            if num:
                full = re.sub(r'\D', '', str(num))
                c = COUNTRY_INFO.get(country_key, {"flag": "🌍", "name": "International"})
                await status.edit_text(f"🚀 **NUMBER ALLOCATED**\n\n📍 {c['flag']} {c['name']}\n📱 `+{full}`\n⏳ Waiting...", parse_mode=ParseMode.MARKDOWN)
                return
        await status.edit_text("❌ Failed. Try again.")

async def text_handler(update: Update, context):
    text = update.message.text.upper()
    if "GET NUMBER" in text:
        await update.message.reply_text("👇 দেশ সিলেক্ট করুন:", reply_markup=get_country_keyboard())
    elif "2FA" in text:
        await update.message.reply_text("🔧 Maintenance Mode.")
    elif "LIVE OTP" in text:
        await update.message.reply_text("📡 Live OTP", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View Live", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]]))

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    async def post_init(application):
        application.create_task(fetch_live_ranges())
        logger.info("Bot Started")

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)
