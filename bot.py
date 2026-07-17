import logging
import re
import os
import httpx
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

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 🌟 ━━━━━━ [ GET NUMBER ] ━━━━━━ 🌟 🔥")],
    [KeyboardButton("🔑 ⚡ ━━━━━━ [ 2FA CODE ] ━━━━━━ ⚡ 🔑")]
], resize_keyboard=True, is_persistent=True)

def get_flag_and_name(number_str):
    if not number_str:
        return "International", "🌍"
    clean_num = re.sub(r'\D', '', str(number_str))
    country_map = {
        "261": ("Madagascar", "🇲🇬"), "224": ("Guinea", "🇬🇳"), "232": ("Sierra Leone", "🇸🇱"),
        "236": ("Central African Rep.", "🇨🇫"), "880": ("Bangladesh", "🇧🇩"), "91": ("India", "🇮🇳"),
        "62": ("Indonesia", "🇮🇩"), "63": ("Philippines", "🇵🇭"), "84": ("Vietnam", "🇻🇳"),
        "225": ("Ivory Coast", "🇨🇮"), "380": ("Ukraine", "🇺🇦")
    }
    for prefix, info in country_map.items():
        if clean_num.startswith(prefix):
            return info
    return (f"Country (+{clean_num[:3]})", "🌍")

async def call_website_api_async(payload):
    try:
        url = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json", "Accept": "application/json"}
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers, timeout=15.0)
            if r.status_code == 200:
                return r.json()
    except Exception as e:
        logging.error(f"Async API Error: {e}")
    return None

async def start(update: Update, context: CallbackContext):
    if not update.message: return
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"✨ **WELCOME TO SUPER FIRE OTP ENGINE** ✨\n👤 `User:` **{name}**\n⚡ `System:` **Premium Multi-Route Active**\n═══════════════════════\n🤖 *Select an option from the menu below to begin:*",
        reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN
    )

async def show_services_menu(message_obj):
    buttons = [
        [InlineKeyboardButton("🔷 🌐 FACEBOOK (ফেসবুক) 🌐 🔷", callback_data="service_facebook")],
        [InlineKeyboardButton("🔷 📸 INSTAGRAM (ইনস্টাগ্রাম) 📸 🔷", callback_data="service_instagram")]
    ]
    await message_obj.reply_text("⚡ **SELECT YOUR PREMIUM SERVICE** ⚡\n━━━━━━━━━━━━━━━━━━━━━━━\n👇 *কোন সার্ভিসের নাম্বার প্রয়োজন সেটি সিলেক্ট করুন:*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def show_ranges_menu(message_obj, service_name):
    api_response = await call_website_api_async({"action": "getnum", "service": service_name, "type": "ranges"})
    buttons = []
    if api_response and api_response.get("meta", {}).get("status") == "ok":
        ranges_list = api_response.get("data", {}).get("ranges", [])
        for r in ranges_list:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{service_name}_{r}")])
    if not buttons:
        for r in ["26134", "224655", "23274"]:
            c_name, c_flag = get_flag_and_name(r)
            buttons.append([InlineKeyboardButton(f"🔷 {c_flag} {c_name} ({r}) 🔷", callback_data=f"range_{service_name}_{r}")])
    buttons.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services")])
    await message_obj.reply_text(f"🔷 **LIVE ACTIVE RANGES FOR {service_name.upper()}** 🔷\n━━━━━━━━━━━━━━━━━━━━━━━\n👇 *সার্ভার থেকে প্রাপ্ত সচল রেঞ্জ সিলেক্ট করুন:*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def check_otp_loop(context: CallbackContext, chat_id, number_id, original_msg_id, number_str, c_flag, c_name, service_name):
    clean_num = str(number_str).replace('+', '')
    for _ in range(30): 
        await asyncio.sleep(7) 
        api_response = await call_website_api_async({"action": "getotp", "id": number_id})
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            otp_code = api_response.get("data", {}).get("otp")
            if otp_code:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=original_msg_id, text=f"🟢 **VIP OTP RECEIVED SUCCESSFULLY** 🟢\n━━━━━━━━━━━━━━━━━━━━━━━\n🌍 `Region:` **{c_flag} {c_name}**\n📱 `Number:` `+{clean_num}`\n━━━━━━━━━━━━━━━━━━━━━━━\n🎁 **YOUR OTP CODE:**\n\n⚡⚡ `{otp_code}` ⚡⚡\n\n⏱️ `Status:` **Done! Verification Completed.**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Change Number 🔄", callback_data=f"service_{service_name}")]]) , parse_mode=ParseMode.MARKDOWN)
                return
    await context.bot.edit_message_text(chat_id=chat_id, message_id=original_msg_id, text=f"❌ **OTP Timeout!** কোনো ওটিপি কোড পাওয়া যায়নি।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Another Number 🔄", callback_data=f"service_{service_name}")]]))

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query: return
    data = query.data
    if data == "back_to_services":
        await query.answer(); await query.message.delete(); await show_services_menu(query.message)
    elif data.startswith("service_"):
        await query.answer(); await query.message.delete(); await show_ranges_menu(query.message, data.split("_")[1])
    elif data.startswith("range_"):
        await query.answer(); parts = data.split("_"); service_name = parts[1]; selected_range = parts[2]
        status_msg = await query.message.reply_text("⏳ **Connecting to Server...**")
        api_response = await call_website_api_async({"action": "getnum", "service": service_name, "range": selected_range})
        await status_msg.delete()
        if api_response and api_response.get("meta", {}).get("status") == "ok":
            nd = api_response.get("data", {}); num = nd.get("full_number") or nd.get("number"); nid = nd.get("id")
            if num:
                c_name, c_flag = get_flag_and_name(num); clean_num = str(num).replace('+', '')
                await query.message.delete()
                sent_msg = await query.message.reply_text(f"⚡ **NUMBER ASSIGNED** ⚡\n📱 `Number:` `+{clean_num}`\n⏱️ `Status:` **Waiting for OTP...**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Change Number 🔄", callback_data=f"service_{service_name}")]]), parse_mode=ParseMode.MARKDOWN)
                asyncio.create_task(check_otp_loop(context, query.message.chat_id, nid, sent_msg.message_id, clean_num, c_flag, c_name, service_name))
                return
        await query.message.reply_text("❌ **API Error:** সার্ভিস থেকে নম্বর পাওয়া যাচ্ছে না।")

async def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text: return
    if "GET NUMBER" in update.message.text: await show_services_menu(update.message)
    elif "2FA CODE" in update.message.text: await update.message.reply_text("📥 **Enter your 2FA Secret Key:**", parse_mode=ParseMode.MARKDOWN)

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
