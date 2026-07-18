import logging
import httpx
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")
GROUP_ID = -1003666001785 # আপনার গ্রুপ আইডি এখানে আপডেট করা হয়েছে

logging.basicConfig(level=logging.INFO)

async def is_user_in_group(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("✨ **WELCOME TO SUPER FIRE OTP** ✨\n\nবটটি ব্যবহার করতে প্রথমে আমাদের গ্রুপে জয়েন করুন: @SUPERFIREOTP", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔥 🌟 GET NUMBER 🌟 🔥")]], resize_keyboard=True))

async def check_otp_loop(context: CallbackContext, chat_id, number_id, original_msg_id, number_str, service_name):
    for _ in range(30):
        await asyncio.sleep(7)
        async with httpx.AsyncClient() as client:
            api_response = await client.post("https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum", json={"action": "getotp", "id": number_id}, headers={"X-API-Key": API_KEY})
            if api_response.status_code == 200:
                data = api_response.json().get("data", {})
                otp = data.get("otp")
                if otp:
                    # ইউজারকে ওটিপি পাঠানো
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=original_msg_id, text=f"✅ **OTP RECEIVED:** `{otp}`")
                    # গ্রুপে ওটিপি ফরওয়ার্ড করা
                    await context.bot.send_message(chat_id=GROUP_ID, text=f"🚀 **New OTP Found!**\n📱 Number: {number_str}\n🔑 OTP: `{otp}`")
                    return
    await context.bot.edit_message_text(chat_id=chat_id, message_id=original_msg_id, text="❌ **Timeout! কোনো ওটিপি পাওয়া যায়নি।**")

async def handle_message(update: Update, context: CallbackContext):
    if not await is_user_in_group(context, update.effective_user.id):
        await update.message.reply_text("⚠️ **আপনি গ্রুপে জয়েন করেননি!** বট ব্যবহার করতে প্রথমে আমাদের গ্রুপে জয়েন করুন: @SUPERFIREOTP")
        return
    
    if "GET NUMBER" in update.message.text:
        buttons = [[InlineKeyboardButton("FACEBOOK", callback_data="service_facebook")]]
        await update.message.reply_text("সার্ভিস সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("service_"):
        service = query.data.split("_")[1]
        async with httpx.AsyncClient() as client:
            api_res = await client.post("https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum", json={"action": "getnum", "service": service}, headers={"X-API-Key": API_KEY})
        
        data = api_res.json().get("data", {})
        num = data.get("number")
        nid = data.get("id")
        
        if num:
            msg = await query.message.reply_text(f"📱 নম্বর: {num}\n⏳ ওটিপির জন্য অপেক্ষা করুন...")
            asyncio.create_task(check_otp_loop(context, query.message.chat_id, nid, msg.message_id, num, service))
        else:
            await query.message.reply_text("❌ নম্বর পাওয়া যায়নি।")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
