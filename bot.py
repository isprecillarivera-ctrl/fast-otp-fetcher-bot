import logging
import re
import os
import httpx
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"
active_otp_tasks = {}

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

# নির্দিষ্ট ৩টি দেশের ম্যাপিং (যেটি আপনি পছন্দ করেছেন)
COUNTRY_MAP = {
    "232": {"name": "Sierra Leone", "flag": "🇸🇱"},
    "224": {"name": "Guinea", "flag": "🇬🇳"},
    "225": {"name": "Ivory Coast", "flag": "🇨🇮"}
}

async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except: return False

async def call_api(endpoint, payload=None):
    url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(url, json=payload, headers=headers) if payload else await client.get(url, headers=headers)
            return r.json() if r.status_code == 200 else None
        except: return None

async def show_ranges(msg, service):
    res = await call_api("liveaccess")
    kb = []
    seen = set()
    # শুধুমাত্র সেই ৩টি দেশের রেঞ্জ ফিল্টার করা হচ্ছে
    for s in res.get("services", []):
        if s["sid"].lower() == service.lower():
            for r in s["ranges"]:
                p = re.sub(r'\D', '', str(r))[:3]
                if p in COUNTRY_MAP and p not in seen:
                    seen.add(p)
                    # বাটন: পতাকা + দেশের নাম
                    kb.append([InlineKeyboardButton(f"{COUNTRY_MAP[p]['flag']} {COUNTRY_MAP[p]['name']}", callback_data=f"range_{service}_{r}")])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    await msg.reply_text("Select Country:", reply_markup=InlineKeyboardMarkup(kb))

async def handle_callback(update, context):
    query = update.callback_query
    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(query.message.chat_id, "স্বাগতম! আপনি ভেরিফাইড ইউজার।", reply_markup=main_keyboard)
        else: await query.answer("আপনি গ্রুপগুলোতে জয়েন করেননি!", show_alert=True)
    elif query.data.startswith("range_"):
        parts = query.data.split("_")
        status_msg = await query.message.edit_text("⚡ _Allocating..._")
        res = await call_api("getnum", {"range": parts[2]})
        if res and res.get("meta", {}).get("status") == "ok":
            num_data = res["data"]
            num = num_data.get("full_number", num_data.get("number"))
            p = re.sub(r'\D', '', str(num))[:3]
            c = COUNTRY_MAP.get(p, {"name": "Premium", "flag": "🌍"})
            btn = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chgnum_{parts[1]}_{parts[2]}")]]
            await status_msg.edit_text(f"🚀 **NUMBER:** `+{re.sub(r'\D', '', str(num))}`\n📍 **COUNTRY:** {c['flag']} {c['name']}\n⏳ **STATUS:** Waiting for OTP...", reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.MARKDOWN)
            active_otp_tasks[query.message.chat_id] = asyncio.create_task(check_otp(context, query.message.chat_id, num_data["id"], status_msg.message_id, num))
    elif query.data.startswith("service_"):
        await query.message.delete()
        await show_ranges(query.message, query.data.split("_")[1])

async def check_otp(context, chat_id, number_id, msg_id, number):
    for _ in range(40):
        await asyncio.sleep(5)
        res = await call_api("getotp", {"action": "getotp", "id": int(number_id)})
        otp = res.get("otp") or res.get("data", {}).get("otp") if res else None
        if otp:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"👑 **SUCCESS!**\n🔑 **CODE:** `{otp}`", parse_mode=ParseMode.MARKDOWN)
            return
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="❌ **TIMEOUT**")

# বাকি সব ফাংশন আগের মতোই থাকবে...
