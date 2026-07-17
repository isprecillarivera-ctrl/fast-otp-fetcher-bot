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

DATA_FILE = "authorized_users.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
], resize_keyboard=True, persistent=True, is_persistent=True)

join_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/EASY_MARKETING1")],
    [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/EASY_METHOD1")],
    [InlineKeyboardButton("✅ Verify", callback_data="verify")]
])

async def start(update: Update, context: CallbackContext):
    if update.effective_user.id in authorized_users:
        await update.message.reply_text("✅ Welcome! Use the buttons below.", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("🔒 Join channels and click Verify", reply_markup=join_keyboard)

async def verify(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    authorized_users.add(user_id)
    save_authorized(authorized_users)

    await query.message.delete()
    await context.bot.send_message(
        chat_id=user_id,
        text="✅ **ভেরিফাই সফল হয়েছে!**\n\nএখন বাটনগুলো ব্যবহার করুন।",
        reply_markup=main_keyboard
    )

async def handle_message(update: Update, context: CallbackContext):
    if update.effective_user.id not in authorized_users:
        await update.message.reply_text("🔒 প্রথমে Verify করুন।", reply_markup=join_keyboard)
        return

    text = update.message.text
    if text == "🎲 GET NUMBER":
        await update.message.reply_text("🔍 Service Select করুন (এখনো বাকি)", reply_markup=main_keyboard)
    elif text == "🔐 2FA CODE":
        await update.message.reply_text("🔐 2FA কোড পাঠান...", reply_markup=main_keyboard)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Bot Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
