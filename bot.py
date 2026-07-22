import logging
import re
import os
import httpx
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

live_ranges = {}

async def call_api(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=15) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload or {}, headers=headers)
            return r.json() if r.status_code == 200 else None
    except:
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
            logger.info(f"Loaded: {list(live_ranges.keys())}")
        await asyncio.sleep(25)

def get_keyboard():
    buttons = []
    for sid in live_ranges.keys():
        # দেশের নাম দেখানোর চেষ্টা
        name = sid.upper().replace("_", " ")
        if "sl" in sid or "sierra" in sid:
            name = "🇸🇱 Sierra Leone"
        elif "gn" in sid or "guinea" in sid:
            name = "🇬🇳 Guinea"
        elif "bj" in sid or "benin" in sid:
            name = "🇧🇯 Benin"
        elif "ci" in sid:
            name = "🇨🇮 Ivory Coast"
        elif "mg" in sid:
            name = "🇲🇬 Madagascar"
        else:
            name = f"🌍 {name}"
        buttons.append([InlineKeyboardButton(name, callback_data=f"range_{sid}")])
    return InlineKeyboardMarkup(buttons) if buttons else InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="refresh")]])

async def start(update: Update, context):
    await update.message.reply_text("✅ স্বাগতম!", reply_markup=main_keyboard)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "refresh":
        await fetch_live_ranges()
        await query.message.edit_text("✅ Updated!")
        return
    if query.data.startswith("range_"):
        sid = query.data.split("_", 1)[1]
        status = await query.message.edit_text("⚡ Allocating...")
        res = await call_api("getnum", "POST", {"range": "1", "service": sid})
        if res and res.get("meta", {}).get("status") == "ok":
            num = res.get("data", {}).get("full_number") or res.get("data", {}).get("number")
            if num:
                full = re.sub(r'\D', '', str(num))
                await status.edit_text(f"🚀 **NUMBER ALLOCATED**\n📱 `+{full}`\n⏳ Waiting...", parse_mode=ParseMode.MARKDOWN)
                return
        await status.edit_text("❌ Failed.")

async def text_handler(update: Update, context):
    if "GET NUMBER" in update.message.text.upper():
        await update.message.reply_text("👇 দেশ সিলেক্ট করুন:", reply_markup=get_keyboard())

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
