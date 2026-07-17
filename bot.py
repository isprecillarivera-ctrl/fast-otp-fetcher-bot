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
SMS_API_KEY = os.getenv("SMS_API_KEY", "MURAD_F455C219DCF80BC50E1E696E")

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

twofa_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📘 Facebook 2FA", callback_data="2fa_fb")],
    [InlineKeyboardButton("📸 Instagram 2FA", callback_data="2fa_ig")],
    [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
])

# SMS API Helper (fastxotps.com)
def get_number(service: str):
    try:
        url = "https://fastxotps.com/api/get_number"  # Adjust endpoint if needed
        payload = {
            "key": SMS_API_KEY,
            "service": service.lower()
        }
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("number"), data.get("id")
        return None, None
    except Exception as e:
        logger.error(f"Get number failed: {e}")
        return None, None

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in authorized_users:
        await update.message.reply_text(
            "✨ **SUPER FIRE OTP BOT** ✨\n💰 Balance: 0.0 BDT\n\nনিচের অপশন ব্যবহার করুন:",
            reply_markup=main_keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            "🔒 **চ্যানেলে জয়েন করে Verify করুন**",
            reply_markup=join_keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "verify_user":
        authorized_users.add(user_id)
        save_authorized_users(authorized_users)
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ **ভেরিফাই সফল হয়েছে!**\n\n✨ Welcome to SUPER FIRE OTP BOT!",
            reply_markup=main_keyboard
        )

    elif data.startswith("num_"):
        service = "facebook" if "fb" in data else "instagram"
        number, order_id = get_number(service)
        if number:
            await query.message.edit_text(
                f"✅ **{service.title()} Number:**\n`{number}`\n\nOrder ID: {order_id}\nOTP আসার জন্য অপেক্ষা করুন...",
                reply_markup=num_keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text("❌ নাম্বার জেনারেট করতে সমস্যা হয়েছে। পরে চেষ্টা করুন।", reply_markup=num_keyboard)

    elif data.startswith("2fa_"):
        service = "Facebook" if "fb" in data else "Instagram"
        await query.message.edit_text(
            f"📌 **{service} 2FA** সিলেক্ট হয়েছে।\nকোড আসলে এখানে পাঠান।",
            reply_markup=twofa_keyboard
        )

    elif data == "back_main":
        await query.message.edit_text("🏠 মেইন মেনু", reply_markup=main_keyboard)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if user_id not in authorized_users:
        await update.message.reply_text("🔒 প্রথমে Verify করুন।", reply_markup=join_keyboard)
        return

    if text == "🎲 GET NUMBER":
        await update.message.reply_text("🔍 নাম্বার সার্ভিস সিলেক্ট করুন:", reply_markup=num_keyboard)
    elif text == "🔐 2FA CODE":
        await update.message.reply_text("🔐 2FA সার্ভিস সিলেক্ট করুন:", reply_markup=twofa_keyboard)
    else:
        otps = OTP_PATTERN.findall(text)
        if otps and update.message.chat.type != "private":
            for otp in otps:
                alert = (
                    f"🔥 **FAST OTP DETECTED!** 🔥\n"
                    f"**OTP:** `{otp}`\n"
                    f"**User:** {update.effective_user.first_name}\n"
                    f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                try:
                    await context.bot.send_message(YOUR_CHAT_ID, alert, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    logger.error(f"OTP send failed: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 SUPER FIRE OTP BOT সফলভাবে চালু হয়েছে...")
    app.run_polling()

if __name__ == '__main__':
    main()
