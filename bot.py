import logging
import re
import json
import os
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID") or 0)
SMS_API_KEY = os.getenv("SMS_API_KEY", "MURAD_F455C219DCF80BC50E1E696E")

if not TOKEN:
    raise ValueError("BOT_TOKEN missing!")

OTP_PATTERN = re.compile(r'\b(\d{4,8})\b')
DATA_FILE = "authorized_users.json"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def load_authorized_users():
    try:
        with open(DATA_FILE, 'r') as f:
            return set(json.load(f))
    except:
        return set()

def save_authorized_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(list(users), f, indent=2)

authorized_users = load_authorized_users()

main_keyboard = ReplyKeyboardMarkup([ [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")] ], resize_keyboard=True, is_persistent=True)

join_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/EASY_MARKETING1")],
    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/EASY_METHOD1")],
    [InlineKeyboardButton("✅ Verify", callback_data="verify_user")]
])

num_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📘 Facebook Number", callback_data="num_fb")],
    [InlineKeyboardButton("📸 Instagram Number", callback_data="num_ig")],
    [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
])

twofa_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📘 Facebook 2FA", callback_data="2fa_fb")],
    [InlineKeyboardButton("📸 Instagram 2FA", callback_data="2fa_ig")],
    [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
])

def get_number(service: str):
    try:
        # fastxotps.com API - adjust if needed
        url = f"https://fastxotps.com/api/get_number?key={SMS_API_KEY}&service={service.lower()}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("number"), data.get("id")
        logger.warning(f"API Response: {response.text}")
        return None, None
    except Exception as e:
        logger.error(f"Get number failed: {e}")
        return None, None

async def start(update: Update, context: CallbackContext):
    if update.effective_user.id in authorized_users:
        await update.message.reply_text("✨ **SUPER FIRE OTP BOT** ✨\n💰 Balance: 0.0 BDT", reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("🔒 Join channels & Verify", reply_markup=join_keyboard, parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "verify_user":
        authorized_users.add(user_id)
        save_authorized_users(authorized_users)
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(user_id, "✅ Verified! Use menu below.", reply_markup=main_keyboard)

    elif data in ["num_fb", "num_ig"]:
        service_name = "Facebook" if "fb" in data else "Instagram"
        number, order_id = get_number(service_name.lower())
        if number:
            await query.message.edit_text(f"✅ **{service_name} Number:** `{number}`\nID: {order_id}\n\nOTP আসলে অটো ফরওয়ার্ড হবে।", parse_mode=ParseMode.MARKDOWN, reply_markup=num_keyboard)
        else:
            await query.message.edit_text("❌ নাম্বার পাওয়া যায়নি। পরে চেষ্টা করুন।", reply_markup=num_keyboard)

    # ... (অন্যান্য callback)

async def handle_message(update: Update, context: CallbackContext):
    # OTP detection logic remains
    text = update.message.text.strip()
    if update.effective_user.id not in authorized_users:
        await update.message.reply_text("Verify first.", reply_markup=join_keyboard)
        return
    # ... rest of logic

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 Bot Started")
    app.run_polling()

if __name__ == '__main__':
    main()
