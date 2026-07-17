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

# 📱 প্রফেশনাল কিবোর্ড
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📱 GET NUMBER"), KeyboardButton("🔑 2FA CODE")]
], resize_keyboard=True, is_persistent=True)

# 🌍 অরিজিনাল নম্বরের শুরু দেখে সঠিক দেশ ও পতাকা খোঁজার ইঞ্জিন
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
    return (f"Country (+{clean_num[:3]})", "🌍")

# 📡 প্রোভাইডারের এপিআই থেকে বাস্তব রেঞ্জ ও নম্বর তুলে আনার ফাংশন
def call_sms_api(payload):
    try:
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        # আপনার এপিআই প্রোভাইডারের সার্ভারে রিকোয়েস্ট পাঠানো হচ্ছে
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logging.error(f"API Error: {e}")
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

# 🔄 সার্ভার থেকে লাইভ আসা আসল রেঞ্জ দিয়ে মেনু তৈরি
async def show_ranges_menu(message_obj):
    # আপনার সার্ভার থেকে বর্তমানের সচল ও অরিজিনাল রেঞ্জগুলোর লিস্ট চাওয়া হচ্ছে
    api_response = call_sms_api({"action": "get_active_ranges", "service": "facebook"})
    
    buttons = []
    
    if api_response and api_response.get("meta", {}).get("status") == "ok":
        ranges_list = api_response.get("data", {}).get("ranges", [])
        
        for r in ranges_list:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"📡 {c_flag} {c_name} ({r})", callback_data=f"range_{r}")])
    
    # এপিআই রেসপন্স খালি থাকলে বা কোনো রেঞ্জ না পাওয়া গেলে ইউজারকে অ্যালার্ট দেবে
    if not buttons:
        await message_obj.reply_text("⚠️ **বর্তমানে সার্ভারে কোনো লাইভ রেঞ্জ খালি নেই!** অনুগ্রহ করে একটু পরে আবার চেষ্টা করুন বা রিফ্রেশ দিন।",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 ⚡ REFRESH ⚡ 🔄", callback_data="refresh_ranges")]]))
        return
        
    buttons.append([InlineKeyboardButton("🔄 ⚡ REFRESH RANGES ⚡ 🔄", callback_data="refresh_ranges")])
    
    await message_obj.reply_text(
        f"🔥 **LIVE ACTIVE RANGES FOR FACEBOOK**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *সার্ভার থেকে প্রাপ্ত সচল রেঞ্জ সিলেক্ট করুন:*",
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
        status_msg = await query.message.reply_text("⏳ **Connecting to Server... Requesting Original Number...**")
        
        # 📡 এপিআই-তে আসল সিলেক্টেড রেঞ্জ পাঠিয়ে একদম অরিজিনাল নম্বর আনা হচ্ছে
        api_response = call_sms_api({"range": selected_range, "action": "get_number", "service": "facebook"})
        await status_msg.delete()
        
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            number_data = api_response.get("data", {})
            original_number = number_data.get("full_number")
            number_id = number_data.get("id")
            
            c_name, c_flag = get_flag_and_name(original_number)
            
            # 💎 প্রফেশনাল ট্যাপ-টু-কপি লেআউট
            number_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"📋 🔗 +{original_number} (Tap to Copy)", callback_data=f"copy_{original_number}")],
                [InlineKeyboardButton("🔄 Request Another Number", callback_data=f"range_{selected_range}")],
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
            error_msg = api_response.get("meta", {}).get("message", "কোনো নম্বর পাওয়া যায়নি।") if api_response else "সার্ভার রেসপন্স করছে না।"
            await query.message.reply_text(f"❌ **API Error:** {error_msg}")
        
    elif data.startswith("copy_"):
        num = data.split("_")[1]
        await query.answer(text=f"✅ +{num} Copied to Clipboard!", show_alert=True)

async def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return
    text = update.message.text

    if text == "📱 GET NUMBER":
        await show_ranges_menu(update.message)
        
    elif text == "🔑 2FA CODE":
        await update.message.reply_text(
            "🔑 **SECURE 2FA CODE DECRYPTER**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📥 অনুগ্রহ করে আপনার অ্যাকাуন্টের **2FA Secret Key**টি নিচে পেস্ট করুন।",
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
    
    print("🚀 100% ORIGINAL API ENGINE LIVE...")
    app.run_polling()

if __name__ == '__main__':
    main()
