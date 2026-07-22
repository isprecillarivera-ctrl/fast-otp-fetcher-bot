import logging
import re
import os
import httpx
import asyncio
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")

if not TOKEN or not API_KEY:
    raise ValueError("BOT_TOKEN বা SMS_API_KEY .env ফাইলে নেই!")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

active_otp_tasks = {}
live_ranges = {}

# দেশের তথ্য
COUNTRY_INFO = {
    "sl": {"flag": "🇸🇱", "name": "Sierra Leone"},
    "gn": {"flag": "🇬🇳", "name": "Guinea"},
    "ci": {"flag": "🇨🇮", "name": "Ivory Coast"},
    "mg": {"flag": "🇲🇬", "name": "Madagascar"},
    "bj": {"flag": "🇧🇯", "name": "Benin"},
    "int": {"flag": "🌍", "name": "International"},
}

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

# ==================== API কল ====================
async def call_website_api_async(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload or {}, headers=headers)
            
            logger.info(f"API {endpoint} Status: {r.status_code}")
            if r.status_code == 200:
                return r.json()
            return None
    except Exception as e:
        logger.error(f"API Error ({endpoint}): {e}")
        return None

# ==================== লাইভ রেঞ্জ লোড ====================
async def fetch_live_ranges():
    global live_ranges
    while True:
        try:
            res = await call_website_api_async("liveaccess", method="GET")
            if res:
                live_ranges = {}
                services = res.get("services") or res.get("data") or []
                if isinstance(services, list):
                    for service in services:
                        sid = str(service.get("sid", "")).lower().strip()
                        ranges = service.get("ranges", [])
                        if sid and ranges:
                            live_ranges[sid] = ranges
                            logger.info(f"✅ Loaded service: {sid} ({len(ranges)} ranges)")
                logger.info(f"🎯 Total live ranges loaded: {len(live_ranges)}")
            else:
                logger.warning("liveaccess API খালি রেসপন্স দিয়েছে")
        except Exception as e:
            logger.error(f"fetch_live_ranges error: {e}")
        await asyncio.sleep(25)

# ==================== ডায়নামিক কীবোর্ড ====================
def get_dynamic_keyboard():
    if not live_ranges:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Ranges লোড করুন", callback_data="refresh_ranges")
        ]])
    
    buttons = []
    for sid, ranges in list(live_ranges.items())[:15]:
        country_key = sid.split("_")[0] if "_" in sid else sid[:2]
        info = COUNTRY_INFO.get(country_key.lower(), {"flag": "🌍", "name": sid.upper()})
        for i in range(min(3, len(ranges))):
            callback = f"range_{sid}_{i+1}"
            text = f"{info['flag']} {info['name']} - Range {i+1}"
            buttons.append([InlineKeyboardButton(text, callback_data=callback)])
    return InlineKeyboardMarkup(buttons)

# ==================== হ্যান্ডলার ====================
async def start(update: Update, context):
    await update.message.reply_text("✅ স্বাগতম! নিচের বাটন থেকে সার্ভিস বেছে নিন।", reply_markup=main_keyboard)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "refresh_ranges":
        await query.message.edit_text("🔄 Ranges লোড হচ্ছে, অপেক্ষা করুন...")
        await fetch_live_ranges()
        await query.message.edit_text("✅ Ranges আপডেট হয়েছে!\nআবার GET NUMBER চাপুন।", reply_markup=get_dynamic_keyboard())
        return

    if query.data.startswith("range_"):
        parts = query.data.split("_")
        service_id = parts[1]
        range_value = parts[2]

        status_msg = await query.message.edit_text("⚡ Number অ্যালোকেট করা হচ্ছে...")

        res = await call_website_api_async("getnum", method="POST", payload={
            "range": range_value,
            "service": service_id
        })

        if res and res.get("meta", {}).get("status") == "ok":
            data = res.get("data", {})
            num = data.get("full_number") or data.get("number")
            if num:
                full_num = re.sub(r'\D', '', str(num))
                country_key = service_id.split("_")[0] if "_" in service_id else service_id[:2]
                country = COUNTRY_INFO.get(country_key.lower(), {"flag": "🌍", "name": "International"})
                
                btn = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chgnum_{service_id}_{range_value}")]]
                await status_msg.edit_text(
                    f"🚀 **NUMBER ALLOCATED**\n\n"
                    f"📍 COUNTRY: {country['flag']} {country['name']}\n"
                    f"📱 PHONE: `+{full_num}`\n"
                    f"⏳ STATUS: Waiting for OTP...",
                    reply_markup=InlineKeyboardMarkup(btn),
                    parse_mode=ParseMode.MARKDOWN
                )
                return

        await status_msg.edit_text("❌ নাম্বার পাওয়া যায়নি। অন্য রেঞ্জ চেষ্টা করুন।")

async def text_handler(update: Update, context):
    text = update.message.text.upper()
    if "GET NUMBER" in text:
        await update.message.reply_text(
            "👇 **দেশ সিলেক্ট করুন:**",
            reply_markup=get_dynamic_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    elif "2FA" in text:
        await update.message.reply_text("🔧 Maintenance Mode.")
    elif "LIVE OTP" in text:
        await update.message.reply_text(
            "📡 Live OTP দেখুন:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View Live", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]])
        )

# ==================== বট চালু ====================
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    async def post_init(application):
        application.create_task(fetch_live_ranges())
        logger.info("🤖 SUPER FIRE OTP Bot Started Successfully!")

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)
