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

def get_country_keyboard():
    buttons = []
    for code, data in ALLOWED_COUNTRIES.items():
        buttons.append([InlineKeyboardButton(f"{data['flag']} {data['name']}", callback_data=f"range_{code}_1")])
    return InlineKeyboardMarkup(buttons)

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
        return True

async def check_otp(context, chat_id, number):
    full_number = re.sub(r'\D', '', str(number))
    logger.info(f"🔍 Monitoring OTP for +{full_number}")
    seen_otps = set()
    try:
        for attempt in range(900):
            await asyncio.sleep(2)
            res = await call_website_api_async("success-otp-info", method="GET")
            if res and "data" in res and "otps" in res.get("data", {}):
                for item in res["data"]["otps"]:
                    item_num = re.sub(r'\D', '', str(item.get("number", "")))
                    if item_num == full_number or item_num.endswith(full_number[-8:]):
                        otp = item.get("otp") or item.get("code") or item.get("sms")
                        if otp and otp not in seen_otps:
                            seen_otps.add(otp)
                            country = ALLOWED_COUNTRIES.get(full_number[:3])
                            c_flag = country["flag"] if country else "🌍"
                            c_name = country["name"] if country else "Unknown"
                            visible = full_number[:6] if len(full_number) > 6 else full_number
                            hidden_number = f"+{visible}{'*' * (len(full_number) - len(visible))}"

                            public_text = f"""
🌟 **SUPER FIRE OTP** 🌟
🔥 **NEW OTP RECEIVED** 🔥
{c_flag} **{c_name}**
📱 **Number:** `{hidden_number}`
🔑 **OTP Code:** `{otp}`
🕒 **Time:** {datetime.now().strftime('%I:%M:%S %p')}
                            """
                            keyboard = InlineKeyboardMarkup([
                                [InlineKeyboardButton("🔄 OTP বটে নিয়ে আসুন", url=f"https://t.me/{BOT_USERNAME}")],
                                [InlineKeyboardButton("📢 আপডেট গ্রুপে যান", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")]
                            ])

                            await context.bot.send_message(chat_id=OTP_CHANNEL, text=public_text.strip(), parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
                            await context.bot.send_message(chat_id=chat_id, text=f"✅ **OTP RECEIVED SUCCESSFULLY!**\n📱 `+{number}`\n🔑 `{otp}`", parse_mode=ParseMode.MARKDOWN)
                            return
    except asyncio.CancelledError:
        logger.info(f"OTP monitoring cancelled for +{full_number}")
    except Exception as e:
        logger.error(f"OTP check error: {e}")
    finally:
        active_otp_tasks.pop(chat_id, None)

async def start(update: Update, context):
    user_id = update.effective_user.id
    if not await is_user_subscribed(context, user_id):
        kb = [
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify")]
        ]
        await update.message.reply_text("বটটি ব্যবহার করতে প্রথমে আমাদের গ্রুপগুলোতে জয়েন করুন এবং নিচে ভেরিফাই বাটনে ক্লিক করুন।", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text("আপনি ভেরিফাইড ইউজার। নিচে থেকে সার্ভিস সিলেক্ট করুন।", reply_markup=main_keyboard)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text="স্বাগতম! আপনি এখন সকল সুবিধা ব্যবহার করতে পারবেন।", reply_markup=main_keyboard)
        else:
            await query.answer("আপনি এখনও জয়েন করেননি!", show_alert=True)
        return

    if query.data.startswith("range_") or query.data.startswith("chgnum_"):
        chat_id = query.message.chat_id
        if chat_id in active_otp_tasks:
            task = active_otp_tasks[chat_id]
            if not task.done():
                task.cancel()
            active_otp_tasks.pop(chat_id, None)

        parts = query.data.split("_")
        range_value = parts[2] if len(parts) > 2 else "1"

        status_msg = await query.message.edit_text("⚡ Allocating number...")

        res = await call_website_api_async("getnum", method="POST", payload={"range": range_value})

        if res and res.get("meta", {}).get("status") == "ok":
            data = res.get("data", {})
            num = data.get("full_number") or data.get("number") or data.get("national_number")
           
            if num:
                c = ALLOWED_COUNTRIES.get(str(num)[:3])
                if not c:
                    c = {"flag": "🌍", "name": "International"}
                btn = [[InlineKeyboardButton("🔄 Change Number", callback_data=f"chgnum_{parts[1] if len(parts)>1 else '1'}_{range_value}")]]
                await status_msg.edit_text(
                    f"🚀 **NUMBER ALLOCATED**\n\n"
                    f"📍 COUNTRY: {c['flag']} {c['name']}\n"
                    f"📱 PHONE: `+{re.sub(r'\D', '', str(num))}`\n"
                    f"⏳ STATUS: Waiting for OTP...",
                    reply_markup=InlineKeyboardMarkup(btn),
                    parse_mode=ParseMode.MARKDOWN
                )
                active_otp_tasks[chat_id] = asyncio.create_task(check_otp(context, chat_id, num))
                return

        await status_msg.edit_text("❌ Failed to allocate number. Try another country.")

async def text_handler(update: Update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        return await start(update, context)

    text = update.message.text.upper()

    if "GET NUMBER" in text:
        await update.message.reply_text("👇 **দেশ সিলেক্ট করুন:**", reply_markup=get_country_keyboard(), parse_mode=ParseMode.MARKDOWN)
    elif "2FA" in text:
        await update.message.reply_text("🔧 Maintenance Mode.")
    elif "LIVE OTP" in text:
        await update.message.reply_text("📡 Live OTP দেখতে:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View Live", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")]]))

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    async def post_init(application):
        application.create_task(auto_refresh_ranges())

    app.post_init = post_init

    logger.info("🤖 SUPER FIRE OTP Bot Started Successfully!")
    app.run_polling(drop_pending_updates=True)
