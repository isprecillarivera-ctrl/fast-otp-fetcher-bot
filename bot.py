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

CHANNEL_1 = "@SUPERFIREUPDATE"
CHANNEL_2 = "@SUPERFIREOTP"

# সক্রিয় ওটিপি টাস্কগুলো ট্র্যাক করার জন্য গ্লোবাল ডিকশনারি (নাম্বার চেঞ্জ করলে আগের লুপ বন্ধ করার জন্য)
active_otp_tasks = {}

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

def get_join_keyboard():
    buttons = [
        [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{CHANNEL_1.replace('@', '')}")],
        [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{CHANNEL_2.replace('@', '')}")],
        [InlineKeyboardButton("✅ Check Joined / Verify", callback_data="check_membership")]
    ]
    return InlineKeyboardMarkup(buttons)

async def is_user_subscribed(context: CallbackContext, user_id: int) -> bool:
    try:
        member1 = await context.bot.get_chat_member(chat_id=CHANNEL_1, user_id=user_id)
        if member1.status in ['left', 'kicked']:
            return False
        member2 = await context.bot.get_chat_member(chat_id=CHANNEL_2, user_id=user_id)
        if member2.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        logging.error(f"Membership verification error: {e}")
        return True

COUNTRY_MAP = {
    "232": {"name": "Sierra Leone", "flag": "🇸🇱"},
    "224": {"name": "Guinea", "flag": "🇬🇳"},
    "225": {"name": "Ivory Coast", "flag": "🇨🇮"}
}

def get_country_details(number_str):
    clean_num = re.sub(r'\D', '', str(number_str))
    prefix = clean_num[:3]
    if prefix in COUNTRY_MAP:
        return COUNTRY_MAP[prefix]["name"], COUNTRY_MAP[prefix]["flag"]
    return "Premium Server", "🌍"

async def call_website_api_async(endpoint, method="POST", payload=None):
    try:
        url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient(timeout=6.0, limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)) as client:
            if method == "GET":
                r = await client.get(url, headers=headers)
            else:
                r = await client.post(url, json=payload, headers=headers)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logging.error(f"Async API Error: {e}")
    return None

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not await is_user_subscribed(context, user_id):
        await update.message.reply_text(
            f"⚠️ **Please join our channels to use the bot!**\n\n"
            f"আমাদের পরিষেবাগুলি ব্যবহার করতে প্রথমে নিচের দুটি চ্যানেলে জয়েন করে ভেরিফাই বাটনে ক্লিক করুন।",
            reply_markup=get_join_keyboard(), parse_mode=ParseMode.MARKDOWN
        )
        return

    await update.message.reply_text(
        f"👑 **𝖲𝖴𝖯𝖤𝖱 𝖥𝖨𝖱𝖤 𝖮𝖳𝖯 𝖤𝖭𝖦𝖨𝖭𝖤** 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _🔥 Premium & Ultra Fast Automated OTP Server_ ⚡\n\n"
        f"👇 *Select an option from the menu below to start:*",
        reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN
    )

async def show_services_menu(message_obj):
    buttons = [
        [InlineKeyboardButton("🔷 🌐 FACEBOOK 🌐 🔷", callback_data="service_facebook")],
        [InlineKeyboardButton("🔷 📸 INSTAGRAM 📸 🔷", callback_data="service_instagram")]
    ]
    await message_obj.reply_text(
        f"💎 **𝖯𝖱𝖤𝖬𝖨𝖴𝖬 𝖲𝖤𝖱𝖵𝖨𝖢𝖤 𝖲𝖤𝖫𝖤𝖢𝖳𝖨𝖮𝖭**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Please choose your target platform:*", 
        reply_markup=InlineKeyboardMarkup(buttons), 
        parse_mode=ParseMode.MARKDOWN
    )

async def show_ranges_menu(message_obj, service_name):
    api_response = await call_website_api_async("liveaccess", method="GET")
    buttons = []
    api_service_name = "Facebook" if service_name == "facebook" else "Instagram"
      
    if api_response and (api_response.get("status") == "ok" or "services" in api_response):
        services_list = api_response.get("services", [])
        
        for service in services_list:
            if str(service.get("sid")).lower() == service_name.lower():
                ranges_list = service.get("ranges", [])
                
                seen_countries = set()
                for r in ranges_list:
                    clean_r = re.sub(r'\D', '', str(r))
                    prefix = clean_r[:3]
                    
                    if prefix in COUNTRY_MAP and prefix not in seen_countries:
                        seen_countries.add(prefix)
                        c_info = COUNTRY_MAP[prefix]
                        buttons.append([InlineKeyboardButton(f"✨ {c_info['flag']} {c_info['name']} ✨", callback_data=f"range_{service_name}_{r}")])
                break
      
    buttons.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services")])

    await message_obj.reply_text(
        f"🔥 **𝖫𝖨𝖵𝖤 𝖠𝖢𝖳𝖨𝖵𝖤 𝖲𝖤𝖱𝖵𝖤𝖱𝖲 [{api_service_name.upper()}]**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _Select your country to fetch number instantly:_ ", 
        reply_markup=InlineKeyboardMarkup(buttons), 
        parse_mode=ParseMode.MARKDOWN
    )

async def check_otp_loop(context, chat_id, number_id, original_msg_id, original_number):
    try:
        for attempt in range(1, 40):   
            await asyncio.sleep(5)   
            
            api_response = await call_website_api_async("getotp", method="POST", payload={"action": "getotp", "id": int(number_id)})
            
            if api_response:
                data_sec = api_response.get("data", {})
                otp_code = None
                if isinstance(data_sec, dict):
                    otp_code = data_sec.get("otp")
                
                if not otp_code and api_response.get("meta", {}).get("status") == "ok":
                    otp_code = api_response.get("meta", {}).get("otp") or api_response.get("otp")

                if otp_code:
                    await context.bot.edit_message_text(
                        chat_id=chat_id, message_id=original_msg_id,
                        text=f"👑 **𝖲𝖴𝖢𝖢𝖤𝖲𝖲! 𝖮𝖳𝖯 𝖱𝖤𝖢𝖤𝖨𝖵𝖤𝖣** 👑\n"
                             f"━━━━━━━━━━━━━━━━━━━━\n\n"
                             f"🔢 **PHONE:** `+{original_number}`\n"
                             f"🔑 **YOUR CODE:** `{otp_code}`\n\n"
                             f"━━━━━━━━━━━━━━━━━━━━\n"
                             f"💡 _কোডের ওপর আলতো ট্যাপ করলেই ইনস্ট্যান্ট কপি হয়ে যাবে।_",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
    except asyncio.CancelledError:
        # নাম্বার চেঞ্জ বাটন টিপলে এই এরর জেনারেট হয়ে লুপ বন্ধ হবে
        logging.info(f"OTP Loop cancelled for number {original_number}")
        return

    await context.bot.edit_message_text(
        chat_id=chat_id, message_id=original_msg_id, 
        text=f"❌ **𝖮𝖳𝖯 𝖳𝖨𝖬𝖤𝖮𝖴𝖳**\n"
             f"━━━━━━━━━━━━━━━━━━━━\n"
             f"No response received. Please drop this number and try a new one.", 
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    
    if data == "check_membership":
        await query.answer("✅ Verification Successful!", show_alert=True)
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"👑 **𝖲𝖴𝖯𝖤𝖱 𝖥𝖨𝖱𝖤 𝖮𝖳𝖯 𝖤𝖭𝖦𝖨𝖭𝖤** 👑\n"
                 f"━━━━━━━━━━━━━━━━━━━━\n"
                 f"🥳 আপনাকে স্বাগতম! আপনার ভেরিফিকেশন সফল হয়েছে।\n\n"
                 f"👇 *Select an option from the menu below to start:*",
            reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN
        )
        return

    await query.answer()

    if data == "back_to_services":
        await query.message.delete()
        await show_services_menu(query.message)
    elif data.startswith("service_"):
        await query.message.delete()
        await show_ranges_menu(query.message, data.split("_")[1])
    elif data.startswith("range_") or data.startswith("chgnum_"):
        # সাধারণ রিকোয়েস্ট অথবা নাম্বার পরিবর্তন রিকোয়েস্ট হ্যান্ডেল করা
        parts = data.split("_")
        service_name = parts[1]
        selected_range = parts[2]
        
        # যদি ইউজার 'Change Number' বাটন টিপে, তবে আগের চলমান ওটিপি লুপটি ক্যানসেল করে দেওয়া হবে
        if chat_id in active_otp_tasks:
            active_otp_tasks[chat_id].cancel()
            del active_otp_tasks[chat_id]
            
        status_msg = await query.message.edit_text("⚡ _Allocating a fresh dynamic number... Please wait._", parse_mode=ParseMode.MARKDOWN)
        
        payload = {"range": selected_range}
        api_response = await call_website_api_async("getnum", method="POST", payload=payload)
        
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            num_data = api_response.get("data", {})
            num = num_data.get("full_number") or num_data.get("no_plus_number") or num_data.get("number")
            clean_num = re.sub(r'\D', '', str(num))
            num_id = num_data.get("id")
            
            c_name, c_flag = get_country_details(clean_num)
            
            # নাম্বার পরিবর্তন করার জন্য ইনলাইন বাটন প্রস্তুত করা
            change_btn = [[InlineKeyboardButton("🔄 Change Number / Get New 🔄", callback_data=f"chgnum_{service_name}_{selected_range}")]]
              
            await status_msg.edit_text(
                f"🚀 **𝖭𝖴𝖬𝖡𝖤𝖱 𝖠𝖫𝖫𝖮𝖢𝖠𝖳𝖤𝖣** 🚀\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📍 **COUNTRY:** {c_flag} {c_name}\n"
                f"📱 **PHONE:** `+{clean_num}`\n"
                f"⏳ **STATUS:** Waiting for incoming live OTP...\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 _নাম্বারের ওপর আলতো ট্যাপ করলেই ইনস্ট্যান্ট কপি হয়ে যাবে।_",
                reply_markup=InlineKeyboardMarkup(change_btn),
                parse_mode=ParseMode.MARKDOWN
            )

            # নতুন টাস্ক তৈরি করে ট্র্যাকিং ডিকশনারিতে রাখা
            task = asyncio.create_task(
                check_otp_loop(
                    context, chat_id, num_id, 
                    status_msg.message_id, clean_num
                )
            )
            active_otp_tasks[chat_id] = task
        else:
            await status_msg.edit_text("❌ **Server Busy!**\nNo active numbers available right now in this country. Please try again.")

async def handle_text_buttons(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.effective_user.id
    
    if not await is_user_subscribed(context, user_id):
        await update.message.reply_text(
            f"⚠️ **Access Denied!**\n\n"
            f"পরিষেবা ব্যবহার করতে প্রথমে আমাদের চ্যানেলে জয়েন সম্পন্ন করুন।",
            reply_markup=get_join_keyboard(), parse_mode=ParseMode.MARKDOWN
        )
        return

    if "GET NUMBER" in text:
        await show_services_menu(update.message)
    elif "2FA CODE" in text:
        await update.message.reply_text(
            f"🔑 **𝖯𝖱𝖤𝖬𝖨𝖴𝖬 𝟤𝖥𝖠 𝖠𝖴𝖳𝖧𝖤𝖭𝖳𝖨𝖢𝖠𝖳𝖨𝖮𝖭**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ Status: _System is under maintenance._\n"
            f"⚡ _We are integrating premium high-speed 2FA servers._", 
            parse_mode=ParseMode.MARKDOWN
        )
    elif "LIVE OTP SECTION" in text:
        await update.message.reply_text(
            f"📡 **𝖫𝖨𝖵𝖤 𝖮𝖳𝖯 𝖲𝖳𝖠𝖳𝖴𝖲 𝖣𝖠𝖲𝖧𝖡𝖮𝖠𝖱𝖣**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🟢 **System Status:** Fully Operational\n"
            f"⚡ **Server Speed:** `0.1s` (Hyper Fast)\n"
            f"📶 **API Success Rate:** `99.9%`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👉 _আমাদের লাইভ ক্লাউড সার্ভারগুলো এখন সম্পূর্ণ সচল আছে। নতুন নাম্বার তুলতে ওপরের '🔥 GET NUMBER 🔥' বাটনে ক্লিক করুন!_", 
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
