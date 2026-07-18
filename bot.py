import logging
import httpx
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")
GROUP_ID = -1003666001785 
BASE_URL = "https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum"

logging.basicConfig(level=logging.INFO)

# কি-বোর্ড লেআউট
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 🌟 ━━━━━━ [ GET NUMBER ] ━━━━━━ 🌟 🔥")],
    [KeyboardButton("📢 LIVE OTP"), KeyboardButton("🔒 2FA OPTION")]
], resize_keyboard=True)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("✨ **WELCOME TO SUPER FIRE OTP ENGINE** ✨\n\nনিচের বাটন থেকে আপনার প্রয়োজনীয় অপশনটি সিলেক্ট করুন।", reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    if "GET NUMBER" in text:
        buttons = [
            [InlineKeyboardButton("🔵 FACEBOOK (Range: 26134XXX) 🔵", callback_data="26134XXX")],
            [InlineKeyboardButton("📸 INSTAGRAM (Range: 26135XXX) 📸", callback_data="26135XXX")]
        ]
        await update.message.reply_text("👇 **সার্ভিস সিলেক্ট করুন (আপনার রেঞ্জ অনুযায়ী):**", reply_markup=InlineKeyboardMarkup(buttons))
    elif "LIVE OTP" in text:
        await update.message.reply_text("📢 **লাইভ ওটিপি আপডেট গ্রুপ:** https://t.me/SUPERFIREOTP")
    elif "2FA OPTION" in text:
        await update.message.reply_text("🔒 **2FA Security Center.**")

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    # নতুন API অনুযায়ী 'range' পাঠাতে হবে
    selected_range = query.data
    
    async with httpx.AsyncClient() as client:
        # API এন্ডপয়েন্ট এবং হেডারে API KEY
        res = await client.post(BASE_URL, 
                                json={"range": selected_range}, 
                                headers={"X-API-Key": API_KEY},
                                timeout=15.0)
        
        response_data = res.json()
        
        # নতুন API রেসপন্স স্ট্রাকচার অনুযায়ী ডাটা বের করা
        data = response_data.get("data", {})
        num = data.get("full_number")
        
        if num:
            await query.message.reply_text(f"✅ **নম্বর পাওয়া গেছে:** `{num}`")
            # আপনার গ্রুপে পাঠানোর লজিক এখানে যুক্ত করুন
        else:
            await query.message.reply_text("❌ এই রেঞ্জে বর্তমানে কোনো নম্বর খালি নেই।")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
