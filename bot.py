import logging
import re
import os
import requests
import pyotp
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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 📱 নিচে মেইন কিবোর্ডের ইমোজি ও নাম প্রফেশনাল করা হলো (লুডু আইকন মুক্ত)
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📱 GET NUMBER"), KeyboardButton("🔑 2FA CODE")]
], resize_keyboard=True, is_persistent=True)

# 🌍 নম্বর বা রেঞ্জ থেকে দেশ চেনার ইন্টেলিজেন্ট ম্যাপার
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
        "380": ("Ukraine", "🇺🇦")
    }
    for prefix, info in country_map.items():
        if clean_num.startswith(prefix):
            return info
    return (f"Range (+{clean_num[:3]})", "🌍")

# 📡 আপনার ওয়েবসাইটের সার্ভারে কানেক্ট করার সেন্ট্রাল স্মার্ট ইঞ্জিন
def call_website_api(payload):
    try:
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # আপনার প্রোভাইডারের সার্ভারে JSON ডাটা সহ POST রিকোয়েস্ট পাঠানো হচ্ছে
        logging.info(f"Sending to Website Server: {payload}")
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        
        # রেলওয়ে বা গিটহাব লগ-এ দেখার জন্য সার্ভার রেসপন্স প্রিন্ট
        logging.info(f"Website Server Status Code: {r.status_code}")
        logging.info(f"Raw Website Response Text: {r.text}")
        
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logging.error(f"Critical Connection Error to 2eee7.com: {e}")
    return None

async def start(update: Update, context: CallbackContext):
    if not update.message:
        return
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"✨ **WELCOME TO SUPER FIRE OTP ENGINE** ✨\n"
        f"👤 `User:` **{name}**\n"
        f"⚡ `System:` **Premium Multi-Route Active**\n"
        f"═══════════════════════\n"
        f"🤖 *Select an option from the menu below to begin:*",
        reply_markup=main_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

# 🔄 সার্ভার থেকে লাইভ আসা আসল রেঞ্জ দিয়ে ডাইনামিক ব্লু-মেনু তৈরি
async def show_ranges_menu(message_obj):
    # ট্রাই ১: স্ট্যান্ডার্ড মেথড
    api_response = call_website_api({"action": "get_ranges", "service": "facebook"})
    
    # ট্রাই ২: যদি প্রথমবার সাড়া না দেয়, বিকল্প ফরম্যাটে ট্রাই করা
    if not api_response or api_response.get("meta", {}).get("status") != "ok":
        api_response = call_website_api({"action": "getnum", "service": "facebook"})
        
    buttons = []
    
    # ১. যদি রেসপন্স ডাটা মেটা-স্ট্যাটাস ওকের ভেতরে থাকে
    if api_response and isinstance(api_response, dict):
        data_part = api_response.get("data", {})
        ranges_list = []
        if isinstance(data_part, dict):
            ranges_list = data_part.get("ranges") or data_part.get("live_ranges") or []
        elif isinstance(api_response.get("ranges"), list):
            ranges_list = api_response.get("ranges")

        if ranges_list:
            for r in ranges_list:
                c_name, c_flag = get_flag_and_name(r)
                buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{r}")])
    
    # ❌ এপিআই যদি কোনো ভ্যালিড রেঞ্জ লিস্ট না পাঠায়, তবে ইউজারকে স্পষ্টভাবে অ্যালার্ট দেবে
    if not buttons:
        await message_obj.reply_text(
            "⚠️ **আপনার ওয়েবসাইট থেকে কোনো লাইভ রেঞ্জ পাওয়া যায়নি!**\n"
            "🔍 `কারণ:` এপিআই কী অবৈধ অথবা সার্ভারে বর্তমানে কোনো রেঞ্জ সচল নেই।\n"
            "💻 *অনুগ্রহ করে রেলওয়ে/সার্ভার লগ-এ আসল রেসপন্সটি চেক করুন।*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 ⚡ TRY REFRESH ⚡ 🔄", callback_data="refresh_ranges")]])
        )
        return
        
    buttons.append([InlineKeyboardButton("🔄 ⚡ REFRESH RANGES ⚡ 🔄", callback_data="refresh_ranges")])
    
    await message_obj.reply_text(
        f"🔷 **LIVE ACTIVE RANGES FOR FACEBOOK** 🔷\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *আপনার ওয়েবসাইট থেকে প্রাপ্ত সচল রেঞ্জ:*",
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
        status_msg = await query.message.reply_text("⏳ **Connecting to Website... Requesting Real Number...**")
        
        # আপনার এপিআই প্রোভাইডারের কাছে নম্বর চাওয়ার জন্য পোস্ট বডি
        api_response = call_website_api({"range": selected_range, "action": "get_number", "service": "facebook"})
        await status_msg.delete()
        
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            number_data = api_response.get("data", {})
            original_number = number_data.get("full_number") or number_data.get("number")
            number_id = number_data.get("id")
            
            if original_number:
                c_name, c_flag = get_flag_and_name(original_number)
                
                # 💎 নীল ও সাদা ডিজাইনের আকর্ষণীয় বাটন লেআউট
                number_buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🔷 📋 +{original_number} (Tap to Copy) 🔷", callback_data=f"copy_{original_number}")],
                    [InlineKeyboardButton("🔹 Request Another Number 🔹", callback_data=f"range_{selected_range}")],
                    [InlineKeyboardButton("🌐 Change Country Range 🌐", callback_data="refresh_ranges")]
                ])
                
                await query.message.delete()
                await query.message.reply_text(
                    f"⚡ **NUMBER SUCCESSFULLY ASSIGNED** ⚡\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 `Region:` **{c_flag} {c_name}**\n"
                    f"🆔 `Session ID:` `{number_id}`\n"
                    f"⏱️ `Status:` **Waiting for Real OTP from Website Server...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👇 *নাম্বার কপি করতে নিচের নীল বাটনে চাপ দিন:*",
                    reply_markup=number_buttons,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
                
        await query.message.reply_text("❌ **সার্ভার রেসপন্স ফেইল!** আপনার ওয়েবসাইট এই রেঞ্জে বর্তমানে কোনো আসল নম্বর দিতে পারছে না।")
        
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
    app.run_polling()

if __name__ == '__main__':
    main()
