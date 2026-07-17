import logging
import re
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
YOUR_CHAT_ID = int(os.getenv("YOUR_CHAT_ID"))

if not TOKEN or not YOUR_CHAT_ID:
    raise ValueError("BOT_TOKEN and YOUR_CHAT_ID must be set in .env file")

OTP_PATTERN = re.compile(r'\b(\d{4,8})\b')
DATA_FILE = "authorized_users.json"

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load authorized users
def load_authorized_users():
    try:
        with open(DATA_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_authorized_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(list(users), f, indent=2)

authorized_users = load_authorized_users()

# Keyboards
def get_main_menu_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")]
    ], resize_keyboard=True, persistent=True, one_time_keyboard=False)

def get_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/EASY_MARKETING1")],
        [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/EASY_METHOD1")],
        [InlineKeyboardButton("✅ Verify", callback_data="verify_user")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_services_keyboard():
    keyboard = [
        [InlineKeyboardButton("📘 Facebook", callback_data="service_fb")],
        [InlineKeyboardButton("📸 Instagram", callback_data="service_ig")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_services")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start Command
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in authorized_users:
        await update.message.reply_text(
            "✨ **Welcome to Easy Marketing Support!** ✨\n"
            "💰 Balance: 0.0 BDT\n\n"
            "Use the menu below:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "🔒 **বট ব্যবহার করার আগে নিচের চ্যানেলে জয়েন করুন!**\n\n"
            "জয়েন করে **✅ Verify** বাটনে চাপ দিন।",
            reply_markup=get_join_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

# Callback Handler
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "verify_user":
        authorized_users.add(user_id)
        save_authorized_users(authorized_users)
        
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ **ভেরিফিকেশন সফল হয়েছে!**\n\n✨ Welcome to Easy Marketing Support!",
            reply_markup=get_main_menu_keyboard()
        )

    elif query.data == "service_fb":
        await query.message.edit_text("📘 **Facebook** সার্ভিস সিলেক্ট করা হয়েছে।\n\nনাম্বার জেনারেট হচ্ছে...", 
                                    reply_markup=get_services_keyboard())

    elif query.data == "service_ig":
        await query.message.edit_text("📸 **Instagram** সার্ভিস সিলেক্ট করা হয়েছে।\n\nনাম্বার জেনারেট হচ্ছে...", 
                                    reply_markup=get_services_keyboard())

    elif query.data == "refresh_services":
        await query.message.edit_text("🔄 সার্ভিস লিস্ট আপডেট করা হয়েছে।", reply_markup=get_services_keyboard())

    elif query.data == "back_main":
        await query.message.delete()
        await context.bot.send_message(chat_id=user_id, text="🏠 মেইন মেনুতে ফিরে এসেছেন।", reply_markup=get_main_menu_keyboard())

# Message Handler
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    chat = update.message.chat

    if user_id not in authorized_users:
        await update.message.reply_text(
            "🔒 **প্রথমে চ্যানেলে জয়েন করে Verify করুন।**",
            reply_markup=get_join_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if text == "🎲 GET NUMBER":
        await update.message.reply_text("🔍 **Select Service:**", reply_markup=get_services_keyboard())
        return

    elif text == "🔐 2FA CODE":
        await update.message.reply_text("🔐 আপনার 2FA কোড এখানে পেস্ট করুন বা জেনারেট করুন।")
        return

    # OTP Detection
    otps = OTP_PATTERN.findall(text)
    if otps and chat.type != "private":  # Only detect in groups
        for otp in otps:
            alert = (
                f"🔥 **FAST OTP DETECTED!** 🔥\n\n"
                f"**OTP:** `{otp}`\n"
                f"**গ্রুপ:** {chat.title or 'Private'}\n"
                f"**ইউজার:** {update.effective_user.first_name}\n"
                f"**টাইম:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            try:
                await context.bot.send_message(YOUR_CHAT_ID, alert, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Failed to send OTP alert: {e}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 FAST OTP FETCHER BOT সফলভাবে চালু হয়েছে...")
    logger.info("Bot started successfully")
    app.run_polling()

if __name__ == '__main__':
    main()
