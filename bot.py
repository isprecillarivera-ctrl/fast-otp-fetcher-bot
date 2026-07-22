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

if not TOKEN:
    raise ValueError("BOT_TOKEN not found!")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"
BOT_USERNAME = "SUPER_FIRE_OTP_BOT"

active_otp_tasks = {}
live_ranges = {}  # Dynamic ranges from API

# ==================== COUNTRY INFO ====================
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

# ==================== API CALL ====================
async def call_website_api_async(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload or {}, headers=headers)
            
            logger.info(f"API {endpoint} Status: {r.status_code}")
            if r.status_code != 200:
                logger.error(f"API Error: {r.text}")
                return None
            return r.json()
    except Exception as e:
        logger.error(f"API call error ({endpoint}): {e}")
        return None

# ==================== LIVE RANGES FETCH ====================
async def fetch_live_ranges():
    global live_ranges
    while True:
        try:
            res = await call_website_api_async("liveaccess", method="GET")
            if res and "services" in res:
                live_ranges = {}
                for service in res["services"]:
                    sid = service.get("sid", "").lower()
                    ranges = service.get("ranges", [])
                    live_ranges[sid] = ranges
                logger.info(f"✅ Live ranges updated! Services: {list(live_ranges.keys())}")
            else:
                logger.warning("No live ranges received")
        except Exception as e:
            logger.error(f"Live range fetch error: {e}")
        await asyncio.sleep(30)

# ==================== DYNAMIC KEYBOARD ====================
def get_dynamic_keyboard():
    if not live_ranges:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh Ranges", callback_data="refresh_ranges")
        ]])
    
    buttons = []
    for sid, ranges in live_ranges.items():
        # Determine country
        country_key = sid.split("_")[0] if "_" in sid else sid[:2]
        info = COUNTRY_INFO.get(country_key.lower(), {"flag": "🌍", "name": sid.upper()})
        
        for i, rng in enumerate(ranges[:3]):  # Max 3 ranges per country
            range_id = rng.get("id") or str(i + 1)
            btn_text = f"{info['flag']} {info['name']} - Range {i+1}"
            callback_data = f"range_{sid}_{range_id}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
    
    return InlineKeyboardMarkup(buttons)

# ==================== SUBSCRIPTION CHECK ====================
async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except:
        return True  # Fail open for testing

# ==================== OTP MONITOR ====================
async def check_otp(context, chat_id, number):
    full_number = re.sub(r'\D', '', str(number))
    logger.info(f"🔍 Monitoring OTP for +{full_number}")
    seen_otps = set()
    
    try:
        for _ in range(900):  # 30 minutes
            await asyncio.sleep(2)
            res = await call_website_api_async("success-otp-info", method="GET")
            if res and "data" in res and "otps" in res.get("data", {}):
                for item in res["data"]["otps"]:
                    item_num = re.sub(r'\D', '', str(item.get("number", "")))
                    if item_num == full_number or item_num.endswith(full_number[-8:]):
                        otp = item.get("otp") or item.get("code") or item.get("sms")
                        if otp and otp not in seen_otps:
                            seen_otps.add(otp)
                            # Find country
                            country = {"flag": "🌍", "name": "International"}
                            for sid, info in COUNTRY_INFO.items():
                                if sid in full_number[:5]:
                                    country = info
                                    break
                            
                            visible = full_number[:6] if len(full_number) > 6 else full_number
                            hidden = f"+{visible}{'*' * (len(full_number) - len(visible))}"
                            
                            public_text = f"""
🌟 **SUPER FIRE OTP** 🌟
🔥 **NEW OTP RECEIVED** 🔥
{country['flag']} **{country['name']}**
📱 **Number:** `{hidden}`
🔑 **OTP Code:** `{otp}`
🕒 **Time:** {datetime.now().strftime('%I:%M:%S %p')}
                            """
                            await context.bot.send_message(
                                chat_id=OTP_CHANNEL,
                                text=public_text.strip(),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"✅ **OTP RECEIVED!**\n📱 `+{full_number}`\n🔑 `{otp}`",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            return
    except asyncio.CancelledError:
        logger.info("OTP monitoring cancelled")
    except Exception as e:
        logger.error(f"OTP check error: {e}")
    finally:
        active_otp_tasks.pop(chat_id, None)

# ==================== HANDLERS ====================
async def start(update: Update, context):
    user_id = update.effective_user.id
    if not await is_user_subscribed(context, user_id):
        kb = [
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ Verify", callback_data="verify")]
        ]
        await update.message.reply_text(
            "বট ব্যবহার করতে প্রথমে চ্যানেলে জয়েন করুন।",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    else:
        await update.message.reply_text(
            "✅ আপনি ভেরিফাইড। নিচে থেকে সার্ভিস সিলেক্ট করুন।",
            reply_markup=main_keyboard
        )

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(query.message.chat_id, "স্বাগতম! এখন সব সুবিধা উপভোগ করুন।", reply_markup=main_keyboard)
        else:
            await query.answer("এখনো জয়েন করেননি!", show_alert=True)
        return

    if query.data == "refresh_ranges":
        await fetch_live_ranges()
        await query.message.edit_text("✅ Ranges Refreshed! আবার GET NUMBER চাপুন।")
        return

    if query.data.startswith("range_") or query.data.startswith("chgnum_"):
        chat_id = query.message.chat_id
        
        if chat_id in active_otp_tasks:
            active_otp_tasks[chat_id].cancel()
            active_otp_tasks.pop(chat_id, None)

        parts = query.data.split("_")
        service_id = parts[1]
        range_value = parts[2] if len(parts) > 2 else "1"

        status_msg = await query.message.edit_text("⚡ Number allocating...")

        payload = {
            "range": range_value,
            "service": service_id
        }

        res = await call_website_api_async("getnum", method="POST", payload=payload)

        if res and res.get("meta", {}).get("status") == "ok":
            data = res.get("data", {})
            num = data.get("full_number") or data.get("number") or data.get("national_number")
            
            if num:
                full_num = re.sub(r'\D', '', str(num))
                # Get correct country info
                country_key = service_id.split("_")[0] if "_" in service_id else service_id[:2]
                country = COUNTRY_INFO.get(country_key.lower(), {"flag": "🌍", "name": "International"})

                change_btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Change Number", callback_data=f"chgnum_{service_id}_{range_value}")
                ]])

                await status_msg.edit_text(
                    f"🚀 **NUMBER ALLOCATED**\n\n"
                    f"📍 COUNTRY: {country['flag']} {country['name']}\n"
                    f"📱 PHONE: `+{full_num}`\n"
                    f"⏳ STATUS: Waiting for OTP...",
                    reply_markup=change_btn,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                active_otp_tasks[chat_id] = asyncio.create_task(check_otp(context, chat_id, num))
                return

        await status_msg.edit_text("❌ Failed to allocate number. Try again.")

async def text_handler(update: Update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        return await start(update, context)

    text = update.message.text.upper().strip()
    
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
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("View Live", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")
            ]])
        )

# ==================== MAIN ====================
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
