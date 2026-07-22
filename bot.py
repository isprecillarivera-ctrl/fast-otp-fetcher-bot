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

if not TOKEN or not API_KEY:
    raise ValueError("BOT_TOKEN or SMS_API_KEY missing!")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

async def call_api(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=15) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload or {}, headers=headers)
            return r.json**আমি স্বীকার করছি।**

আপনি ঠিক বলেছেন — আমি বারবার সার্ভিস (Facebook, WhatsApp) দেখাচ্ছি, যেটা আপনি চাননি। আপনি শুধু **দেশ** চান।

আমি এবার **শুধু দেশ** দেখানোর জন্য সরল কোড দিচ্ছি।

### চূড়ান্ত কোড (শুধু দেশ দেখাবে):

```python
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

if not TOKEN or not API_KEY:
    raise ValueError("BOT_TOKEN or SMS_API_KEY missing!")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

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

# শুধু আপনার দেশগুলো
countries = [
    ("🇸🇱 Sierra Leone", "sl"),
    ("🇬🇳 Guinea", "gn"),
    ("🇧🇯 Benin", "bj"),
    ("🇨🇮 Ivory Coast", "ci"),
    ("🇲🇬 Madagascar", "mg"),
]

def get_country_keyboard():
    buttons = []
    for name, code in countries:
        buttons.append([InlineKeyboardButton(name, callback_data=f"country_{code}")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context):
    await update.message.reply_text("✅ স্বাগতম! দেশ সিলেক্ট করুন।", reply_markup=main_keyboard)

async def handle_callback(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("country_"):
        code = query.data.split("_")[1]
        status = await query.message.edit_text("⚡ Number allocating...")
        res = await call_api("getnum", "POST", {"range": "1", "service": code})
        if res and res.get("meta", {}).get("status") == "ok":
            num = res.get("data", {}).get("full_number") or res.get("data", {}).get("number")
            if num:
                full = re.sub(r'\D', '', str(num))
                await status.edit_text(f"🚀 **NUMBER ALLOCATED**\n📱 `+{full}`\n⏳ Waiting for OTP...", parse_mode=ParseMode.MARKDOWN)
                return
        await status.edit_text("❌ Failed. Try again.")

async def text_handler(update: Update, context):
    if "GET NUMBER" in update.message.text.upper():
        await update.message.reply_text("👇 দেশ সিলেক্ট করুন:", reply_markup=get_country_keyboard())

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    async def post_init(application):
        logger.info("Bot Started")

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)
