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

logging.basicConfig(level=logging.INFO)

# মেইন কি-বোর্ড লেআউট
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 🌟 ━━━━━━ [ GET NUMBER ] ━━━━━━ 🌟 🔥")],
    [KeyboardButton("📢 LIVE OTP"), KeyboardButton("🔒 2FA OPTION")]
], resize_keyboard=True)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("✨ **WELCOME TO SUPER FIRE OTP ENGINE** ✨\n\nনিচ থেকে অপশন সিলেক্ট করুন।", reply_markup=main_keyboard)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    if "GET NUMBER" in text:
        buttons = [
            [InlineKeyboardButton("🔵 FACEBOOK 🔵", callback_data="service_facebook")],
            [InlineKeyboardButton("📸 INSTAGRAM 📸", callback_data="service_instagram")]
        ]
        await update.message.reply_text("👇 সার্ভিস সিলেক্ট করুন:", reply_markup=InlineKeyboardMarkup(buttons))
    
    elif "LIVE OTP" in text:
        # সরাসরি আপনার গ্রুপের লিংক অথবা টেক্সট
        await update.message.reply_text(f"📢 লাইভ ওটিপি আপডেট দেখতে আমাদের গ্রুপে থাকুন: https://t.me/SUPERFIREOTP")
        
    elif "2FA OPTION" in text:
        await update.message.reply_text("🔒 **2FA:** আপনি আমাদের এপিআই ব্যবহার করে ওটিপি পাওয়ার পর এখানে টু-ফ্যাক্টর কোড জেনারেট করতে পারবেন।")

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    service = query.data.split("_")[1]
    
    async with httpx.AsyncClient() as client:
        res = await client.post("https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum", json={"action": "getnum", "service": service}, headers={"X-API-Key": API_KEY})
    
    data = res.json().get("data", {})
    num = data.get("number")
    nid = data.get("id")
    
    if num:
        msg = await query.message.reply_text(f"📱 নম্বর: `{num}`\n⏳ ওটিপির জন্য অপেক্ষা করুন...")
        # ওটিপি লুপ
        for _ in range(30):
            await asyncio.sleep(7)
            async with httpx.AsyncClient() as c:
                r = await c.post("https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum", json={"action": "getotp", "id": nid}, headers={"X-API-Key": API_KEY})
                otp = r.json().get("data", {}).get("otp")
                if otp:
                    await context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=msg.message_id, text=f"✅ ওটিপি: `{otp}`")
                    # সরাসরি গ্রুপে পাঠানো
                    await context.bot.send_message(chat_id=GROUP_ID, text=f"🚀 নতুন ওটিপি:\n📱 নম্বর: {num}\n🔑 কোড: {otp}")
                    return
        await context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=msg.message_id, text="❌ সময় শেষ!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
