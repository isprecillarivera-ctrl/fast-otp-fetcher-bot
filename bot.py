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

# 📱 ফিক্সড প্রফেশনাল কিবোর্ড (লুডুর ইমোজি সরিয়ে মোবাইল ও কি-এর সঠিক আইকন দেওয়া হয়েছে)
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📱 GET NUMBER"), KeyboardButton("🔑 2FA CODE")]
], resize_keyboard=True, is_persistent=True)

# 🌍 ফোন নম্বরের শুরু দেখে সঠিক দেশ ও পতাকা খোঁজার লোকাল ডাইনামিক ইঞ্জিন
def get_flag_and_name(number_str):
    if not number_str:
        return "International", "🌍"
    
    clean_num = re.sub(r'\D', '', str(number_str))
    
    country_map = {
        "261": ("Madagascar", "🇲🇬"),
        "224": ("Guinea", "🇬🇳"),
        "232": ("Sierra Leone", "🇸🇱"),
        "236": ("Central African Rep.", "🇨🇫"),
        "880": ("Bangladesh", "🇧🇩"),
        "91":  ("India", "🇮🇳"),
        "62":  ("Indonesia", "🇮🇩"),
        "63":  ("Philippines", "🇵🇭"),
        "84":  ("Vietnam", "🇻🇳"),
        "225": ("Ivory Coast", "🇨🇮"),
        "380": ("Ukraine", "🇺🇦"),
        "92":  ("Pakistan", "🇵🇰"),
        "20":  ("Egypt", "🇪🇬")
    }
    
    for prefix, info in country_map.items():
        if clean_num.startswith(prefix):
            return info
    return ("International Server", "🌍")

# 📡 এপিআই থেকে লাইভ রেঞ্জ বা আসল নম্বর তুলে আনার সেন্ট্রাল ইঞ্জিন
def call_sms_api(payload):
    try:
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        headers = {"X-API-Key": API_KEY}
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        data = r.json()
        if data.get("meta", {}).get("status") == "ok":
            return data.get("data", {})
    except Exception as e:
        logging.error(f"API Connection Error: {e}")
    return None

async def start(update: Update, context: CallbackContext):
    if not update.message:
        return
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"✨ **WELCOME TO SUPER FIRE OTP ENGINE** ✨\n"
        f"📥 `User:` **{name}**\n"
        f"⚡ `System:` **Premium Multi-Route Active**\n"
        f"═══════════════════════\n"
        f"🤖 *Select an option from the menu below to begin:*",
        reply_markup=main_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

# 🔄 এপিআই ডেটা অনুযায়ী ডাইনামিক রেঞ্জ মেনু তৈরি
async def show_ranges_menu(message_obj):
    api_response = call_sms_api({"action": "get_ranges", "service": "facebook"})
    buttons = []
    
    if api_response and "ranges" in api_response:
        for r in api_response["ranges"]:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"📡 {c_flag} {c_name} ({r})", callback_data=f"range_{r}")])
    else:
        fallback_ranges = ["26134", "224655", "23274"]
        for r in fallback_ranges:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"📡 {c_flag} {c_name} ({r})", callback_data=f"range_{r}")])
    
    buttons.append([InlineKeyboardButton("🔄 ⚡ REFRESH RANGES ⚡ 🔄", callback_data="refresh_ranges")])
    
    await message_obj.reply_text(
        f"🔥 **LIVE ACTIVE RANGES FOR FACEBOOK**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *সিলেক্ট করুন কোন দেশের নাম্বার প্রয়োজন:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data

    if data == "refresh_ranges":
        await query.message.delete()
        await show_ranges_menu(query.message)

    elif data.startswith("range_"):
        selected_range = data.split("_")[1]
        status_msg = await query.message.reply_text("⏳ **Connecting to Server... Fetching Original Number...**")
        
        api_response = call_sms_api({"range": selected_range, "action": "get_number"})
        await status_msg.delete()
        
        if api_response and "full_number" in api_response:
            original_number = api_response.get("full_number")
            number_id = api_response.get("id")
            
            c_name, c_flag = get_flag_and_name(original_number)
            
            number_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📋 🔗 +{original_number} (Tap to Copy)", callback_data=f"copy_{original_number}")],
                [InlineKeyboardButton("🔄 Change Number", callback_data=f"range_{selected_range}")],
                [InlineKeyboardButton("🌐 Change Country Range", callback_data="refresh_ranges")]
            ])
            
            await query.message.delete()
            await query.message.reply_text(
                f"⚡ **NUMBER SUCCESSFULLY ASSIGNED** ⚡\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌍 `Region:` **{c_flag} {c_name}**\n"
                f"🆔 `Session ID:` `{number_id}`\n"
                f"⏱️ `Status:` **Waiting for Secure OTP...**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👇 *নাম্বার কপি করতে নিচের বাটনে চাপ দিন:*",
                reply_markup=number_buttons,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.message.reply_text("❌ **Server Busy!** এই রেঞ্জে বর্তমানে কোনো আসল নম্বর খালি নেই। অন্য রেঞ্জ চেষ্টা করুন।")
        
    elif data.startswith("copy_"):
        num = data.split("_")[1]
        await query.answer(text=f"✅ +{num} Copied to Clipboard!", show_alert=True)

async def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return
    text = update.message.text

    # কিবোর্ড টেক্সট ম্যাচিং আপডেট করা হয়েছে
    if text == "📱 GET NUMBER":
        await show_ranges_menu(update.message)
        
    elif text == "🔑 2FA CODE":
        await update.message.reply_text(
            "🔑 **SECURE 2FA CODE DECRYPTER**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📥 অনুগ্রহ করে আপনার অ্যাকাউন্টের **2FA Secret Key**টি নিচে পেস্ট করুন।",
            parse_mode=ParseMode.MARKDOWN
        )

def main():
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN is missing!")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 100% ORIGINAL DYNAMIC ENGINE RUNNING...")
    app.run_polling()

if __name__ == '__main__':
    main()
