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
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # .env এ আপনার টেলিগ্রাম ID দিন

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"
active_otp_tasks = {}
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

# Dynamic Countries
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
        
        async with httpx.AsyncClient(timeout=8.0) as client:
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

# Admin Command to Add Country
async def add_country(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ এই কমান্ড শুধুমাত্র অ্যাডমিন ব্যবহার করতে পারবে।")
        return

    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("ফরম্যাট:\n/addcountry <prefix> <নাম> <ফ্ল্যাগ>\nউদাহরণ: /addcountry 880 Bangladesh 🇧🇩")
            return

        prefix = args[0].strip()
        name = " ".join(args[1:-1])
        flag = args[-1].strip()

        if len(prefix) != 3 or not prefix.isdigit():
            await update.message.reply_text("❌ Prefix অবশ্যই ৩ ডিজিটের হতে হবে।")
            return

        dynamic_countries[prefix] = {"name": name, "flag": flag}
        ALLOWED_COUNTRIES[prefix] = {"name": name, "flag": flag}

        await update.message.reply_text(f"✅ সফলভাবে যোগ হয়েছে!\n\n{flag} {name} ({prefix})")
        logging.info(f"Admin added country: {prefix} - {name}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except:
        return False

# ... (বাকি সব ফাংশন আগের মতো রাখুন - show_countries, handle_callback, text_handler ইত্যাদি)

async def show_countries(msg):
    kb = []
    for prefix, country in dynamic_countries.items():
        kb.append([InlineKeyboardButton(f"{country['flag']} {country['name']}", callback_data=f"range_any_{prefix}")])

    kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    await msg.reply_text("**দেশ সিলেক্ট করুন:**", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)

# ... (অন্যান্য ফাংশন যেমন start, text_handler, handle_callback আগের মতো রাখুন)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcountry", add_country))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    asyncio.create_task(auto_refresh_ranges())

    logging.info("🤖 SUPER FIRE OTP Bot Started with Admin Add Country Feature!")
    app.run_polling(drop_pending_updates=True)
