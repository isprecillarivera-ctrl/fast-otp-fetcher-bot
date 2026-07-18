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

# আপনার দেওয়া দুটি অফিসিয়াল চ্যানেল ইউজারনেম
CHANNEL_1 = "@SUPERFIREUPDATE"
CHANNEL_2 = "@SUPERFIREOTP"

# প্রধান কীবোর্ড লেআউট
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

# চ্যানেল চেক করার জন্য ইনলাইন কীবোর্ড জেনারেটর (স্ক্রিনশটের মতো ডিজাইন)
def get_join_keyboard():
    buttons = [
        [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{CHANNEL_1.replace('@', '')}")],
        [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{CHANNEL_2.replace('@', '')}")],
        [InlineKeyboardButton("✅ Check Joined / Verify", callback_data="check_membership")]
    ]
    return InlineKeyboardMarkup(buttons)

# ইউজার চ্যানেলে জয়েন আছে কিনা তা চেক করার মূল ফাংশন
async def is_user_subscribed(context: CallbackContext, user_id: int) -> bool:
    try:
        # ১ম চ্যানেল চেক
        member1 = await context.bot.get_chat_member(chat_id=CHANNEL_1, user_id=user_id)
        if member1.status in ['left', 'kicked']:
            return False
            
        # ২য় চ্যানেল চেক
        member2 = await context.bot.get_chat_member(chat_id=CHANNEL_2, user_id=user_id)
        if member2.status in ['left', 'kicked']:
            return False
            
        return True
    except Exception as e:
        logging.error(f"Membership check error: {e}")
        # যদি বট চ্যানেলে অ্যাডমিন না থাকে তবে এরর এড়াতে True রিটার্ন করবে
        return True

def get_flag_and_name(number_str):
    clean_num = re.sub(r'\D', '', str(number_str))
    if not clean_num:
        return "International", "🌍"
      
    country_map = {
        "224": ("Guinea", "🇬🇳"),
        "232": ("Sierra Leone", "🇸🇱"),
        "261": ("Madagascar", "🇲🇬"),
        "225": ("Ivory Coast", "🇨🇮"),
        "236": ("Central African Rep.", "🇨🇫"),
        "880": ("Bangladesh", "🇧🇩"),
        "91": ("India", "🇮🇳"),
        "380": ("Ukraine", "🇺🇦"),
        "992": ("Tajikistan", "🇹🇯"),
        "251": ("Ethiopia", "🇪🇹"),
        "229": ("Benin", "🇧🇯")
    }
    
    for prefix, info in country_map.items():
        if clean_num.startswith(prefix):
            return info[0], info[1]
            
    return f"Country (+{clean_num[:3]})", "🌍"

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
    user_id = update.effective_user.id
    
    # প্রথমে জয়েন চেক করা হচ্ছে
    if not await is_user_subscribed(context, user_id):
        await update.message.reply_text(
            f"⚠️ **Please join our channels to use the bot!**\n\n"
            f"আমাদের পরিষেবাগুলি ব্যবহার করতে প্রথমে নিচের দুটি চ্যানেলে জয়েন করুন এবং ভেরিফাই বাটনে ক্লিক করুন।",
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
    ALLOWED_COUNTRY_PREFIXES = ["232", "224", "225"]
      
    if api_response and (api_response.get("status") == "ok" or "services" in api_response):
        services_list = api_response.get("services", [])
        
        for service in services_list:
            if str(service.get("sid")).lower() == service_name.lower():
                ranges_list = service.get("ranges", [])
                for r in ranges_list:
                    clean_r = re.sub(r'\D', '', str(r))
                    if any(clean_r.startswith(prefix) for prefix in ALLOWED_COUNTRY_PREFIXES):
                        c_name, c_flag = get_flag_and_name(clean_r)
                        buttons.append([InlineKeyboardButton(f"✨ {c_flag} {c_name} ({r}) ✨", callback_data=f"range_{service_name}_{r}")])
                break
      
    buttons.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services")])

    await message_obj.reply_text(
        f"🔥 **𝖫𝖨𝖵𝖤 𝖠𝖢𝖳𝖨𝖵𝖤 𝖱𝖠𝖭𝖦𝖤𝖲 [{api_service_name.upper()}]**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _Select your dynamic country server to fetch numbers:_ ", 
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
                    text=f"👑 **𝖮𝖳𝖯 𝖱𝖤𝖢𝖤𝖨𝖵𝖤𝖣 𝖲𝖴𝖢𝖢𝖤𝖲𝖲𝖥𝖴𝖫𝖫𝖸** 👑\n"
                         f"━━━━━━━━━━━━━━━━━━━━\n\n"
                         f"🔑 **YOUR CODE:** `{otp_code}`\n\n"
                         f"━━━━━━━━━━━━━━━━━━━━\n"
                         f"💡 _নাম্বার বা কোডের ওপর আলতো ট্যাপ করলেই ইনস্ট্যান্ট কপি হয়ে যাবে।_",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

    await context.bot.edit_message_text(
        chat_id=chat_id, message_id=original_msg_id, 
        text=f"❌ **𝖮𝖳𝖯 𝖳𝖨𝖬𝖤𝖮𝖴𝖳**\n"
             f"━━━━━━━━━━━━━━━━━━━━\n"
             f"No response received from the app server. Please drop this number and generate a new one.", 
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # ভেরিফিকেশন বাটন হ্যান্ডেল করা
    if data == "check_membership":
        if await is_user_subscribed(context, user_id):
            await query.answer("✅ Verification Successful! Access Granted.", show_alert=True)
            await query.message.delete()
            await query.message.reply_text(
                f"👑 **𝖲𝖴𝖯𝖤𝖱 𝖥𝖨𝖱𝖤 𝖮𝖳𝖯 𝖤𝖭𝖦𝖨𝖭𝖤** 👑\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🥳 আপনাকে স্বাগতম! আপনার ভেরিফিকেশন সফল হয়েছে।\n\n"
                f"👇 *Select an option from the menu below to start:*",
                reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.answer("❌ You haven't joined both channels yet! Please join first.", show_alert=True)
        return

    # বাকি বাটনগুলোর জন্য চেক করা হবে (ইউজার মাঝখান থেকে লিভ নিলে কাজ করা বন্ধ করবে)
    if not await is_user_subscribed(context, user_id):
        await query.answer("⚠️ Access Denied! You are not in the channels.", show_alert=True)
        return

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
                f"🚀 **𝖭𝖴𝖬𝖡𝖤𝖱 𝖠𝖫𝖫𝖮𝖢𝖠𝖳𝖤𝖣** 🚀\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📱 **PHONE:** `+{clean_num}`\n"
                f"⏳ **STATUS:** Waiting for incoming dynamic OTP...\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💡 _নাম্বার বা কোডের ওপর আলতো ট্যাপ করলেই ইনস্ট্যান্ট কপি হয়ে যাবে।_",
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
    user_id = update.effective_user.id
    
    # টেক্সট বাটনেও প্রথমে জয়েন চেক করা হবে
    if not await is_user_subscribed(context, user_id):
        await update.message.reply_text(
            f"⚠️ **Please join our channels to use the bot!**\n\n"
            f"পরিষেবাটি ব্যবহার করতে প্রথমে নিচের চ্যানেলে জয়েন করুন।",
            reply_markup=get_join_keyboard(), parse_mode=ParseMode.MARKDOWN
        )
        return

    if "GET NUMBER" in text:
        await show_services_menu(update.message)
    elif "2FA CODE" in text:
        await update.message.reply_text(
            f"🔑 **𝟤𝖥𝖠 𝖠𝖴𝖳𝖧𝖤𝖭𝖳𝖨𝖢𝖠𝖳𝖨𝖮𝖭 𝖲𝖤𝖢𝖳𝖨𝖮𝖭**\n"
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
            f"⚡ **Server Speed:** `0.4s` (Ultra Fast)\n"
            f"📶 **API Success Rate:** `99.8%`\n\n"
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
