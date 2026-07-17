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

# 📱 প্রফেশনাল মিনিমাল কিবোর্ড 
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("📱 GET NUMBER"), KeyboardButton("🔑 2FA CODE")]
], resize_keyboard=True, is_persistent=True)

# 🌍 নম্বর থেকে দেশ চেনার লাইভ ট্র্যাকার
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
    return ("International Server", "🌍")

# 📡 ওয়েবসাইট থেকে সরাসরি রিয়েল-টাইম ডাটা আনার ফিক্সড GET মেথড
def fetch_from_website(endpoint, params=None):
    try:
        # বেস ইউআরএল ফিক্সড করা হয়েছে
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        headers = {
            "X-API-Key": API_KEY,
            "Accept": "application/json"
        }
        
        # আপনার ওয়েবসাইটে ডাটা কুয়েরি করার জন্য সঠিক GET রিকোয়েস্ট পাঠানো হচ্ছে
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logging.error(f"Website API Connection Error: {e}")
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

# 🔄 ওয়েবসাইট থেকে লাইভ আসা আসল রেঞ্জ দিয়ে মেনু তৈরি
async def show_ranges_menu(message_obj):
    # আপনার ওয়েবসাইট থেকে সরাসরি ফেসবুকের লাইভ রেঞ্জ রিকোয়েস্ট করা হচ্ছে
    api_response = fetch_from_website("ranges", params={"service": "facebook"})
    
    buttons = []
    
    # ওয়েবসাইট রেসপন্স থেকে ডাইনামিক বাটন জেনারেশন
    if api_response and "ranges" in api_response:
        for r in api_response["ranges"]:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{r}")])
    
    # রেসপন্স লিস্ট যদি কোনো অবজেক্ট বা আলাদা ফিল্ডে থাকে (বিকল্প স্ট্রাকচার হ্যান্ডলিং)
    elif api_response and isinstance(api_response, dict) and "data" in api_response:
        ranges_list = api_response.get("data", {}).get("ranges", [])
        for r in ranges_list:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{r}")])

    if not buttons:
        await message_obj.reply_text("⚠️ **আপনার ওয়েবসাইট থেকে কোনো লাইভ রেঞ্জ পাওয়া যায়নি!** এপিআই কি অথবা সার্ভার স্ট্যাটাস চেক করুন।",
                                     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 ⚡ REFRESH ⚡ 🔄", callback_data="refresh_ranges")]]))
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
        status_msg = await query.message.reply_text("⏳ **Connecting to Website Server... Fetching Real Number...**")
        
        # ওয়েবসাইটে নির্দিষ্ট রেঞ্জ পাঠিয়ে একদম আসল নম্বর জেনারেট করা হচ্ছে
        api_response = fetch_from_website("getnumber", params={"service": "facebook", "range": selected_range})
        await status_msg.delete()
        
        if api_response:
            # প্রোভাইডারের ডাটা ফরম্যাট অনুযায়ী অরিজিনাল নম্বর ও আইডি এক্সট্র্যাক্ট করা
            original_number = api_response.get("number") or api_response.get("data", {}).get("full_number")
            number_id = api_response.get("id") or api_response.get("data", {}).get("id")
            
            if original_number:
                c_name, c_flag = get_flag_and_name(original_number)
                
                # 💎 নীল এবং সাদা থিমের লাক্সারি বাটন লেআউট
                number_buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🔷 📋 +{original_number} (Tap to Copy) 🔷", callback_data=f"copy_{original_number}")],
                    [InlineKeyboardButton("🔹 Change Number 🔹", callback_data=f"range_{selected_range}")],
                    [InlineKeyboardButton("🌐 Change Country Range 🌐", callback_data="refresh_ranges")]
                ])
                
                await query.message.delete()
                await query.message.reply_text(
                    f"⚡ **NUMBER SUCCESSFULLY ASSIGNED** ⚡\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 `Region:` **{c_flag} {c_name}**\n"
                    f"🆔 `Session ID:` `{number_id}`\n"
                    f"⏱️ `Status:` **Waiting for Real OTP from Website...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👇 *নাম্বার কপি করতে নিচের নীল বাটনে চাপ দিন:*",
                    reply_markup=number_buttons,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
                
        await query.message.reply_text("❌ **সার্ভার রেসপন্স ফেইল!** আপনার ওয়েবসাইট বর্তমানে এই রেঞ্জের কোনো আসল নম্বর সাপ্লাই দিতে পারছে না।")
        
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
