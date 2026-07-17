import logging
import re
import os
import requests
import pyotp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
YOUR_CHAT_ID = os.getenv("YOUR_CHAT_ID")
API_KEY = os.getenv("SMS_API_KEY")

try:
    YOUR_CHAT_ID = int(YOUR_CHAT_ID) if YOUR_CHAT_ID else 0
except ValueError:
    YOUR_CHAT_ID = 0

OTP_PATTERN = re.compile(r'\b(\d{4,8})\b')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🛠️ প্রফেশনাল মেইন কিবোর্ড
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📱 GET NUMBER"), KeyboardButton("🔑 2FA GENERATOR")],
    [KeyboardButton("👤 MY ACCOUNT"), KeyboardButton("ℹ️ HELP CENTER")]
], resize_keyboard=True, is_persistent=True)

# 🔵 🟠 প্রিমিয়াম বাটন লেআউট
num_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🟦 Facebook Premium", callback_data="num_fb")],
    [InlineKeyboardButton("🟧 Instagram Premium", callback_data="num_ig")],
    [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
])

# 🌍 লোকাল ফুল কান্ট্রি ও ফ্ল্যাগ ম্যাপার (কোনো এপিআই ফেইলর বা ব্লকিং এর ঝামেলা নেই)
def get_clean_country(number):
    if not number:
        return "Unknown Country 🌐"
    
    clean_num = re.sub(r'\D', '', str(number))
    
    # আন্তর্জাতিক ডায়ালিং রেঞ্জ অনুযায়ী নিখুঁত দেশ ও পতাকা ডাটাবেজ
    country_map = {
        "261": "Madagascar 🇲🇬",
        "232": "Sierra Leone 🇸🇱",
        "236": "Central African Republic 🇨🇫",
        "880": "Bangladesh 🇧🇩",
        "91": "India 🇮🇳",
        "62": "Indonesia 🇮🇩",
        "63": "Philippines 🇵🇭",
        "84": "Vietnam 🇻🇳",
        "225": "Ivory Coast 🇨🇮",
        "380": "Ukraine 🇺🇦",
        "92": "Pakistan 🇵🇰",
        "20": "Egypt 🇪🇬",
        "966": "Saudi Arabia 🇸🇦",
        "971": "UAE 🇦🇪",
        "998": "Uzbekistan 🇺🇿",
        "234": "Nigeria 🇳🇬",
        "254": "Kenya 🇰🇪",
        "1": "USA/Canada 🇺🇸",
        "7": "Russia 🇷🇺",
        "44": "United Kingdom 🇬🇧"
    }
    
    for prefix in sorted(country_map.keys(), key=len, reverse=True):
        if clean_num.startswith(prefix):
            return country_map[prefix]
            
    return f"International (+{clean_num[:3]}) 🌍"

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
    if not update.message:
        return
    context.user_data['waiting_for_2fa'] = False
    await update.message.reply_text(
        "🔥 **WELCOME TO SUPER FIRE OTP BOT** 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 **Status:** Operational & High Speed\n"
        "💰 **Balance:** 0.0 BDT\n"
        "📡 **Engine:** Dynamic Multi-Server API\n\n"
        "🤖 *Select an option from the menu below:*",
        reply_markup=main_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data

    if data == "num_fb":
        status_msg = await query.message.reply_text("⏳ **Connecting to API... Requesting Facebook 🟦 Number...**")
        number, _ = await get_number("26134XXX")
        await status_msg.delete()
        
        if number:
            country = get_clean_country(number)
            # ইমেজের ঝামেলা বাদ দিয়ে সরাসরি প্রিমিয়াম টেক্সট স্টাইল
            await query.message.reply_text(
                f"🔷 **FACEBOOK OFFICIAL SERVICE** 🔷\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍 **Country:** {country}\n"
                f"📱 **Number:** `{number}`\n"
                f"⏱️ **Status:** Waiting for SMS/OTP...\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 *Tip: Click the number to copy instantly.*", 
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.message.reply_text("❌ **Server Busy!** Could not fetch Facebook number. Try again.")

    elif data == "num_ig":
        status_msg = await query.message.reply_text("⏳ **Connecting to API... Requesting Instagram 🟧 Number...**")
        number, _ = await get_number("22507XXX")
        await status_msg.delete()
        
        if number:
            country = get_clean_country(number)
            await query.message.reply_text(
                f"🔸 **INSTAGRAM OFFICIAL SERVICE** 🔸\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍 **Country:** {country}\n"
                f"📱 **Number:** `{number}`\n"
                f"⏱️ **Status:** Waiting for SMS/OTP...\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 *Tip: Click the number to copy instantly.*", 
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.message.reply_text("❌ **Server Busy!** Could not fetch Instagram number. Try again.")

    elif data == "back_main":
        await query.message.edit_text("🏠 **Main Menu Restored**", reply_markup=main_keyboard)

async def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    user_data = context.user_data

    if 'waiting_for_2fa' not in user_data:
        user_data['waiting_for_2fa'] = False

    if text == "📱 GET NUMBER":
        user_data['waiting_for_2fa'] = False
        await update.message.reply_text("🔍 **Select the Premium Service:**", reply_markup=num_keyboard)
    
    elif text == "🔑 2FA GENERATOR":
        user_data['waiting_for_2fa'] = True
        await update.message.reply_text(
            "🔐 **2FA LIVE CODE GENERATOR**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📥 আপনার অ্যাকাউন্টের **2FA Secret Key**টি এখানে মেসেজ করুন।\n\n"
            "⚡ বট সাথে সাথে আপনাকে লাইভ ৬-ডিজিটের কোড বের করে দেবে।", 
            reply_markup=main_keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        return
        
    elif text == "👤 MY ACCOUNT":
        user_data['waiting_for_2fa'] = False
        username = f"@{update.effective_user.username}" if update.effective_user.username else "None"
        await update.message.reply_text(
            f"👤 **PREMIUM USER PROFILE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **User ID:** `{update.effective_user.id}`\n"
            f"📛 **Username:** {username}\n"
            f"💰 **Available Balance:** 0.0 BDT\n"
            f"🛡️ **Account Status:** Active ✅\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif text == "ℹ️ HELP CENTER":
        user_data['waiting_for_2fa'] = False
        await update.message.reply_text(
            "ℹ️ **SYSTEM HELP CENTER**\n\n"
            "🚀 **How to get Dynamic Number:**\n"
            "1. Click **📱 GET NUMBER**.\n"
            "2. Select Facebook 🟦 or Instagram 🟧.\n"
            "3. Copy the number & request OTP.\n\n"
            "🔐 **How to generate 2FA Code:**\n"
            "1. Click **🔑 2FA GENERATOR**.\n"
            "2. Send your 2FA Secret Key directly into the chat.",
            parse_mode=ParseMode.MARKDOWN
        )

    elif user_data.get('waiting_for_2fa'):
        secret = text.strip().replace(" ", "")
        try:
            totp = pyotp.TOTP(secret)
            live_code = totp.now()
            time_remaining = totp.interval - (datetime.now().timestamp() % totp.interval)
            await update.message.reply_text(
                f"🔐 **2FA LIVE CODE GENERATED**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔑 **Live Code:** `{live_code}`\n"
                f"⏳ **Valid For:** {int(time_remaining)} seconds\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await update.message.reply_text("❌ **Invalid Secret Key!** অনুগ্রহ করে সঠিক 2FA Secret Key পাঠান।")
        return

    otps = OTP_PATTERN.findall(text)
    if otps and YOUR_CHAT_ID:
        for otp in otps:
            try:
                await context.bot.send_message(
                    chat_id=YOUR_CHAT_ID, 
                    text=f"🔥 **NEW LIVE OTP RECEIVED!**\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                         f"🔑 **OTP CODE:** `{otp}`\n"
                         f"⏰ **Timestamp:** {datetime.now().strftime('%H:%M:%S')}\n"
                         f"━━━━━━━━━━━━━━━━━━━━━━━━", 
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logging.error(f"Failed to send OTP: {e}")

def main():
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN is missing!")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 BOT ENGINE STARTING...")
    app.run_polling()

if __name__ == '__main__':
    main()
