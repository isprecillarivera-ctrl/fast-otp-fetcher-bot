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

# আপনার দেওয়া লেআউট অনুযায়ী কোনো অতিরিক্ত ইমোজি ছাড়া একদম ক্লিন বাটন
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("GET NUMBER")],
    [KeyboardButton("2FA CODE")],
    [KeyboardButton("LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

def get_flag_and_name(number_str):
    clean_num = re.sub(r'\D', '', str(number_str))
    if not clean_num:
        return None, None
      
    country_map = {
        "224": ("Guinea", "🇬🇳"),
        "232": ("Sierra Leone", "🇸🇱"),
        "261": ("Madagascar", "🇲🇬"),
        "225": ("Ivory Coast", "🇨🇮")
    }
    
    for prefix, info in country_map.items():
        if clean_num.startswith(prefix):
            return info[0], info[1]
            
    return None, None

async def call_website_api_async(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            if method == "GET":
                r = await client.get(url, headers=headers, timeout=15.0)
            else:
                r = await client.post(url, json=payload, headers=headers, timeout=15.0)
                
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logging.error(f"Async API Error: {e}")
    return None

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"🔥 **WELCOME TO SUPER FIRE OTP ENGINE** 🔥\n\n"
        f"⚡ _Fastest & Most Reliable Automated OTP System._\n"
        f"👇 Select an option from the menu below to start:",
        reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN
    )

async def show_services_menu(message_obj):
    buttons = [
        [InlineKeyboardButton("FACEBOOK", callback_data="service_facebook")],
        [InlineKeyboardButton("INSTAGRAM", callback_data="service_instagram")]
    ]
    await message_obj.reply_text("👇 **Select Your Target Service:**", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def show_ranges_menu(message_obj, service_name):
    api_response = await call_website_api_async("liveaccess", method="GET")
    buttons = []
    api_service_name = "Facebook" if service_name == "facebook" else "Instagram"
      
    if api_response and api_response.get("status") == "ok":
        services_list = api_response.get("services", [])
        
        for service in services_list:
            if service.get("sid") == api_service_name:
                ranges_list = service.get("ranges", [])
                for r in ranges_list:
                    c_name, c_flag = get_flag_and_name(r)
                    if c_name and c_flag:
                        buttons.append([InlineKeyboardButton(f"{c_flag} {c_name} ({r})", callback_data=f"range_{service_name}_{r}")])
                break
      
    buttons.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services")])

    await message_obj.reply_text(
        f"🟢 **LIVE ACTIVE RANGES FOR {api_service_name.upper()}**\n"
        f"💡 _Select your preferred dynamic country range below:_ ", 
        reply_markup=InlineKeyboardMarkup(buttons), 
        parse_mode=ParseMode.MARKDOWN
    )

async def check_otp_loop(context, chat_id, number_id, original_msg_id, original_number, service_name):
    for attempt in range(1, 31):   
        await asyncio.sleep(6)   
        api_response = await call_website_api_async("getotp", method="POST", payload={"action": "getotp", "id": number_id})
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            otp_code = api_response.get("data", {}).get("otp")
            if otp_code:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=original_msg_id,
                    text=f"✅ **SUCCESS! OTP RECEIVED** ✅\n\n"
                         f"🔢 **YOUR CODE:** `{otp_code}`\n\n"
                         f"👉 _Click on the code above to copy instantly!_",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

    await context.bot.edit_message_text(
        chat_id=chat_id, message_id=original_msg_id, 
        text="❌ **OTP Timeout!**\nNo response from server. Please drop this and try another number.", 
        parse_mode=ParseMode.MARKDOWN
    )

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
        payload = {"range": parts[2]}
        api_response = await call_website_api_async("getnum", method="POST", payload=payload)
        
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            num_data = api_response.get("data", {})
            num = num_data.get("full_number") or num_data.get("no_plus_number") or num_data.get("number")
            clean_num = re.sub(r'\D', '', str(num))
              
            sent_msg = await query.message.edit_text(
                f"🚀 **NUMBER ALLOCATED SUCCESSFULLY** 🚀\n\n"
                f"📱 **PHONE:** `+{clean_num}`\n"
                f"⏱️ **STATUS:** Waiting for incoming live OTP...\n\n"
                f"📌 _💡 নাম্বারের ওপর চাপ দিলেই এটি অটোমেটিক কপি হয়ে যাবে।_",
                parse_mode=ParseMode.MARKDOWN
            )

            asyncio.create_task(
                check_otp_loop(
                    context, query.message.chat_id, num_data.get("id"), 
                    sent_msg.message_id, clean_num, parts[1]
                )
            )

async def handle_text_buttons(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "GET NUMBER":
        await show_services_menu(update.message)
    elif text == "2FA CODE":
        await update.message.reply_text("🔑 *2FA Code Function is currently processing...*", parse_mode=ParseMode.MARKDOWN)
    elif text == "LIVE OTP SECTION":
        await update.message.reply_text(
            "📡 **LIVE OTP STATUS DASHBOARD** 📡\n\n"
            "🟢 **System Status:** fully Operational\n"
            "⚡ **Server Speed:** 0.4s (Ultra Fast)\n"
            "📶 **Success Rate:** 99.8%\n\n"
            "👉 _আমাদের লাইভ সার্ভারগুলো এখন সম্পূর্ণ সচল আছে। নতুন নাম্বার তুলতে ওপরের 'GET NUMBER' বাটনে ক্লিক করুন!_", 
            parse_mode=ParseMode.MARKDOWN
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_buttons))
    app.run_polling()

if __name__ == '__main__':
    main()
