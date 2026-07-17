import logging
import re
import os
import requests
import pyotp
import asyncio
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

# 🚀 নিচের মূল অপশন দুটিকে আরও বড় ও আকর্ষণীয় গ্লোয়িং ইমোজি দিয়ে সাজানো হলো
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 [ GET NUMBER ] 🔥"), KeyboardButton("🔑 [ 2FA CODE ] 🔑")]
], resize_keyboard=True, is_persistent=True)

# 🌍 দেশ ও পতাকা ম্যাপার
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
    return (f"Country (+{clean_num[:3]})", "🌍")

# 📡 সেন্ট্রাল এপিআই রিকোয়েস্টার
def call_website_api(payload):
    try:
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
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
        f"👤 `User:` **{name}**\n"
        f"⚡ `System:` **Premium Multi-Route Active**\n"
        f"═══════════════════════\n"
        f"🤖 *Select an option from the menu below to begin:*",
        reply_markup=main_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

# 🛍️ ধাপ ১: সার্ভিস সিলেকশন মেনু (কালারফুল এবং আকর্ষণীয় বাটন টেক্সট)
async def show_services_menu(message_obj):
    buttons = [
        [InlineKeyboardButton("🔵 🔵 FACEBOOK (ফেসবুক) 🔵 🔵", callback_data="service_facebook")],
        [InlineKeyboardButton("📸 📸 INSTAGRAM (ইনস্টাগ্রাম) 📸 📸", callback_data="service_instagram")]
    ]
    await message_obj.reply_text(
        f"⚡ **SELECT YOUR PREMIUM SERVICE** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *কোন সার্ভিসের নাম্বার প্রয়োজন সেটি সিলেক্ট করুন:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

# 🔄 ধাপ ২: রেঞ্জ মেনু প্রদর্শন
async def show_ranges_menu(message_obj, service_name):
    api_response = call_website_api({"action": "getnum", "service": service_name, "type": "ranges"})
    buttons = []
    
    if api_response and api_response.get("meta", {}).get("status") == "ok":
        ranges_list = api_response.get("data", {}).get("ranges", [])
        for r in ranges_list:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{service_name}_{r}")])
            
    if not buttons:
        fallback_ranges = ["26134", "224655", "23274"]
        for r in fallback_ranges:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{service_name}_{r}")])
            
    buttons.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services")])
    
    service_title = "🔵 FACEBOOK" if service_name == "facebook" else "📸 INSTAGRAM"
    
    await message_obj.reply_text(
        f"🔷 **LIVE ACTIVE RANGES FOR {service_title}** 🔷\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *সার্ভার থেকে প্রাপ্ত সচল রেঞ্জ সিলেক্ট করুন:*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN
    )

# 📩 ওটিপি রিসিভ করার লুপ
async def check_otp_loop(context: CallbackContext, chat_id, number_id, original_msg_id, number_str, c_flag, c_name):
    for _ in range(30): 
        await asyncio.sleep(10)
        api_response = call_website_api({"action": "getotp", "id": number_id})
        
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            otp_code = api_response.get("data", {}).get("otp")
            if otp_code:
                success_buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🟢 📋 {otp_code} (Tap to Copy) 🟢", callback_data=f"copy_{otp_code}")]
                ])
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=original_msg_id,
                        text=f"✅ **OTP CODE RECEIVED SUCCESSFULLY!** ✅\n"
                             f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                             f"🌍 `Region:` **{c_flag} {c_name}**\n"
                             f"📱 `Number:` `+{number_str}`\n"
                             f"🔑 **YOUR OTP CODE:** `{otp_code}`\n"
                             f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                             f"👇 *ওটিপি কোডটি কপি করতে নিচের বাটনে চাপ দিন:*",
                        reply_markup=success_buttons,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    pass
                return
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=original_msg_id,
            text=f"❌ **OTP Timeout!** কোনো ওটিপি কোড পাওয়া যায়নি।"
        )
    except Exception:
        pass

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data

    if data == "back_to_services":
        await query.message.delete()
        await show_services_menu(query.message)

    elif data.startswith("service_"):
        service_name = data.split("_")[1]
        await query.message.delete()
        await show_ranges_menu(query.message, service_name)

    elif data.startswith("range_"):
        parts = data.split("_")
        service_name = parts[1]
        selected_range = parts[2]
        
        status_msg = await query.message.reply_text("⏳ **Connecting to Server... Fetching Real Number...**")
        api_response = call_website_api({"action": "getnum", "service": service_name, "range": selected_range})
        await status_msg.delete()
        
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            number_data = api_response.get("data", {})
            original_number = number_data.get("full_number") or number_data.get("number")
            number_id = number_data.get("id")
            
            if original_number:
                c_name, c_flag = get_flag_and_name(original_number)
                
                number_buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🟢 📋 +{original_number} (Copy) 🟢", callback_data=f"copy_{original_number}")],
                    [InlineKeyboardButton("🔹 Change Number 🔹", callback_data=f"service_{service_name}")]
                ])
                
                await query.message.delete()
                
                sent_msg = await query.message.reply_text(
                    f"⚡ **NUMBER SUCCESSFULLY ASSIGNED** ⚡\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 `Region:` **{c_flag} {c_name}**\n"
                    f"🆔 `Session ID:` `{number_id}`\n"
                    f"⏱️ `Status:` **Waiting for Real OTP from Website Server...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👇 *নাম্বার কপি করতে নিচের বাটনে চাপ দিন:*",
                    reply_markup=number_buttons,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                asyncio.create_task(check_otp_loop(context, query.message.chat_id, number_id, sent_msg.message_id, original_number, c_flag, c_name))
                return
                
        await query.message.reply_text(f"❌ **API Error:** আপনার ওয়েবসাইট বর্তমানে এই নম্বরটি দিতে পারছে না।")
        
    elif data.startswith("copy_"):
        num = data.split("_")[1]
        await query.answer(text=f"✅ +{num} Copied!", show_alert=True)

async def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return
    text = update.message.text

    if text == "🔥 [ GET NUMBER ] 🔥":
        await show_services_menu(update.message)
        
    elif text == "🔑 [ 2FA CODE ] 🔑":
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
