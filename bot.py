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
YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID"))
API_KEY = os.getenv("SMS_API_KEY")

OTP_PATTERN = re.compile(r'\b(\d{4,8})\b')
DATA_FILE = "authorized_users.json"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

# Professional Keyboard
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
    [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")]
])

async def get_number(service):
    try:
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        payload = {"range": service}
        headers = {"X-API-Key": API_KEY}
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        data = r.json()
        if data.get("meta", {}).get("status") == "ok":
            d = data.get("data", {})
            return d.get("full_number"), d.get("id")
        return None, data.get("meta", {}).get("message")
    except Exception as e:
        return None, str(e)

async def start(update: Update, context: CallbackContext):
    if update.effective_user.id in authorized_users:
        await update.message.reply_text(
            "🌟 **SUPER FIRE OTP BOT** 🌟\n\n"
            "💰 Balance: 0.0 BDT\n"
            "⚡ Fast & Reliable OTP Service",
            reply_markup=main_keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "🔒 **Welcome!**\n\nJoin the channels below and click Verify to start.",
            reply_markup=join_keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "verify_user":
        authorized_users.add(query.from_user.id)
        save_authorized_users(authorized_users)
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(query.from_user.id, "✅ **Successfully Verified!**\n\nUse the buttons below.", reply_markup=main_keyboard)

    elif data == "num_fb":
        await query.message.edit_text("🔄 **Fetching Facebook Number...**")
        number, _ = await get_number("26134XXX")
        if number:
            await query.message.reply_text(f"📘 **Facebook Number**\n`{number}`\n\nReady for OTP.", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text("❌ Failed to get number. Try again.")

    elif data == "num_ig":
        await query.message.edit_text("🔄 **Fetching Instagram Number...**")
        number, _ = await get_number("22507XXX")
        if number:
            await query.message.reply_text(f"📸 **Instagram Number**\n`{number}`\n\nReady for OTP.", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text("❌ Failed to get number. Try again.")

    elif data == "back_main":
        await query.message.edit_text("🏠 **Main Menu**", reply_markup=main_keyboard)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.effective_user.id

    if user_id not in authorized_users:
        await update.message.reply_text("Please verify first.", reply_markup=join_keyboard)
        return

    if text == "🎲 GET NUMBER":
        await update.message.reply_text("🔍 **Choose Service:**", reply_markup=num_keyboard)
    elif text == "🔐 2FA CODE":
        await update.message.reply_text("🔐 **2FA Mode Active**\nSend the code when you receive it.", reply_markup=main_keyboard)

    # OTP Detection
    otps = OTP_PATTERN.findall(text)
    if otps:
        for otp in otps:
            await context.bot.send_message(YOUR_CHAT_ID, f"🔥 **NEW OTP!**\n`{otp}`", parse_mode=ParseMode.MARKDOWN)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 SUPER FIRE OTP BOT - Professional Version Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
