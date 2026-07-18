import logging
import re
import os
import httpx
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# আপনার ছবির লেআউট অনুযায়ী কি-বোর্ড
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 🌟 ━━━━━━ [ GET NUMBER ] ━━━━━━ 🌟 🔥")],
    [KeyboardButton("📢 LIVE OTP"), KeyboardButton("🔒 2FA OPTION")]
], resize_keyboard=True, is_persistent=True)

def get_flag_and_name(number_str):
    clean_num = re.sub(r'\D', '', str(number_str))
    if not clean_num: return "International", "🌍"
    
    country_map = {
        "261": ("Madagascar", "🇲🇬"), "224": ("Guinea", "🇬🇳"),
        "232": ("Sierra Leone", "🇸🇱"), "236": ("Central African Rep.", "🇨🇫"),
        "880": ("Bangladesh", "🇧🇩"), "91": ("India", "🇮🇳"),
        "62": ("Indonesia", "🇮🇩"), "63": ("Philippines", "🇵🇭"),
        "84": ("Vietnam", "🇻🇳"), "225": ("Ivory Coast", "🇨🇮"),
        "380": ("Ukraine", "🇺🇦")
    }
    for prefix, info in country_map.items():
        if clean_num.startswith(prefix): return info
    return (f"Country (+{clean_num[:3]})", "🌍")

async def call_website_api_async(payload):
    try:
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=15.0)
            if r.status_code == 200: return r.json()
    except Exception as e: logging.error(f"Async API Error: {e}")
    return None

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"✨ **WELCOME TO SUPER FIRE OTP ENGINE** ✨\n"
        f"🤖 *Select an option from the menu below:*",
        reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN
    )

async def show_services_menu(message_obj):
    buttons = [
        [InlineKeyboardButton("🔷 🌐 FACEBOOK 🌐 🔷", callback_data="service_facebook")],
        [InlineKeyboardButton("🔷 📸 INSTAGRAM 📸 🔷", callback_data="service_instagram")]
    ]
    await message_obj.reply_text("👇 *Select your service:*", reply_markup=InlineKeyboardMarkup(buttons))

async def show_ranges_menu(message_obj, service_name):
    api_response = await call_website_api_async({"action": "getnum", "service": service_name, "type": "ranges"})
    buttons = []
    if api_response and api_response.get("meta", {}).get("status") == "ok":
        ranges_list = api_response.get("data", {}).get("ranges", [])
        for r in ranges_list:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{service_name}_{r}")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_services")])
    await message_obj.reply_text(f"🔷 *Active Ranges for {service_name.upper()}* 🔷", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def check_otp_loop(context, chat_id, number_id, original_msg_id, original_number, c_flag, c_name, service_name):
    clean_number = re.sub(r'\D', '', str(original_number))
    for _ in range(30): 
        await asyncio.sleep(7) 
        api_response = await call_website_api_async({"action": "getotp", "id": number_id})
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            otp_code = api_response.get("data", {}).get("otp")
            if otp_code:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=original_msg_id,
                    text=f"🟢 **OTP RECEIVED** 🟢\n\n⚡⚡ `{otp_code}` ⚡⚡\n\n*(কপি করতে ওপরের নাম্বারে ট্যাপ করুন)*",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
    await context.bot.edit_message_text(chat_id=chat_id, message_id=original_msg_id, text="❌ *OTP Timeout! Try another number.*", parse_mode=ParseMode.MARKDOWN)

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data == "back_to_services":
        await query.message.delete()
        await show_services_menu(query.message)
    elif data.startswith("service_"):
        await query.message.delete()
        await show_ranges_menu(query.message, data.split("_")[1])
    elif data.startswith("range_"):
        parts = data.split("_")
        api_response = await call_website_api_async({"action": "getnum", "service": parts[1], "range": parts[2]})
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            num_data = api_response.get("data", {})
            num = num_data.get("full_number") or num_data.get("number")
            clean_num = re.sub(r'\D', '', str(num))
            c_name, c_flag = get_flag_and_name(clean_num)
            sent_msg = await query.message.edit_text(
                f"📱 *Number:* `+{clean_num}`\n⏱️ *Waiting for OTP...*",
                parse_mode=ParseMode.MARKDOWN
            )
            asyncio.create_task(check_otp_loop(context, query.message.chat_id, num_data.get("id"), sent_msg.message_id, clean_num, c_flag, c_name, parts[1]))

# আপনার রিকোয়েস্ট অনুযায়ী মেসেজ হ্যান্ডলার আপডেট করা হলো
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    if "GET NUMBER" in text:
        await show_services_menu(update.message)
    elif "LIVE OTP" in text:
        await update.message.reply_text("📢 **লাইভ ওটিপি আপডেট গ্রুপ:** https://t.me/SUPERFIREOTP", parse_mode=ParseMode.MARKDOWN)
    elif "2FA OPTION" in text:
        await update.message.reply_text("🔒 **2FA Security Center.**", parse_mode=ParseMode.MARKDOWN)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    # হ্যান্ডলারটি এখন সব বাটন সঠিকভাবে প্রসেস করবে
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
