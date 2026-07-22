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
    raise ValueError("BOT_TOKEN or SMS_API_KEY missing!")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

active_otp_tasks = {}
live_ranges = {}

# শুধু আপনার পছন্দের দেশগুলো
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

# ==================== API ====================
async def call_website_api_async(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload or {}, headers=headers)
            return r.json() if r.status_code == 200 else None
    except Exception as e:
        logger.error(f"API Error: {e}")
        return None

# ==================== লাইভ রেঞ্জ ====================
async def fetch_live_ranges():
    global live_ranges
    while True:
        res = await call_website_api_async("liveaccess", method="GET")
        if res:
            live_ranges = {}
            services = res.get("services") or res.get("data") or []
            for s in services if isinstance(services, list) else []:
                sid = str(s.get("sid", "")).lower().strip()
                ranges = s.get("ranges", [])
                if sid and ranges:
                    live_ranges[sid] = ranges
            logger.info(f"Loaded {len(live_ranges)} live ranges")
        await asyncio.sleep(25)

# ==================== দেশ ভিত্তিক কীবোর্ড (শুধু যে দেশের রেঞ্জ আছে) ====================
def get_country_keyboard():
    buttons = []
    for sid, ranges in live_ranges.items():
        # দেশের কোড বের করা
        country_key = sid.split("_")[0] if "_" in sid else sid[:2]
        if country_key in COUNTRY_INFO and ranges:  # শুধুমাত্র যাদের রেঞ্জ আছে
            info = COUNTRY_INFO[country_key]
            # প্রতি দেশের জন্য প্রথম রেঞ্জ
            buttons.append([InlineKeyboardButton(
                f"{info['flag']} {info['name']}", 
                callback_data=f"country_{country_key}_{sid}"
            )])
    if not buttons:
        buttons.append([InlineKeyboardButton("🔄 Refresh Ranges", callback_data="refresh_ranges")])
    return InlineKeyboardMarkup(buttons)

# ==================== হ্যান্ডলার ====================
async def start(update: Update, context):
    await update.message.reply_text("✅ স্বাগতম! নিচে থেকে সার্ভিস সিলেক্ট করুন।", reply_markup=main_keyboard)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "refresh_ranges":
        await query.message.edit_text("🔄 Updating ranges...")
        await fetch_live_ranges()
        await query.message.edit_text("✅ Updated! আবার GET NUMBER চাপুন।")
        return

    if query.data.startswith("country_"):
        parts = query.data.split("_")
        country_key = parts[1]
        service_id = parts[2] if len(parts) > 2 else country_key

        status_msg = await query.message.edit_text("⚡ Number allocating...")

        res = await call_website_api_async("getnum", method="POST", payload={
            "range": "1",
            "service": service_id
        })

        if res and res.get("meta", {}).get("status") == "ok":
            data = res.get("data", {})
            num = data.get("full_number") or data.get("number")
            if num:
                full_num = re.sub(r'\D', '', str(num))
                country = COUNTRY_INFO.get(country_key, {"flag": "🌍", "name": "International"})
                btn = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chgnum_{service_id}")]]
                await status_msg.edit_text(
                    f"🚀 **NUMBER ALLOCATED**\n\n"
                    f"📍 COUNTRY: {country['flag']} {country['name']}\n"
                    f"📱 PHONE: `+{full_num}`\n"
                    f"⏳ STATUS: Waiting for OTP...",
                    reply_markup=InlineKeyboardMarkup(btn),
                    parse_mode=ParseMode.MARKDOWN
                )
                return

        await status_msg.edit_text("❌ Failed. Try again or refresh ranges.")

async def text_handler(update: Update, context):
    text = update.message.text.upper()
    if "GET NUMBER" in text:
        if not live_ranges:
            await update.message.reply_text("⏳ Ranges লোড হচ্ছে...\nকয়েক সেকেন্ড পর আবার চেষ্টা করুন।", 
                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="refresh_ranges")]]))
        else:
            await update.message.reply_text("👇 **দেশ সিলেক্ট করুন:**", reply_markup=get_country_keyboard())
    elif "2FA" in text:
        await update.message.reply_text("🔧 Maintenance Mode.")
    elif "LIVE OTP" in text:
        await update.message.reply_text("📡 Live OTP দেখুন:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View Live", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]]))

# ==================== বট চালু ====================
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    async def post_init(application):
        application.create_task(fetch_live_ranges())
        logger.info("🤖 SUPER FIRE OTP Bot Started!")

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)
