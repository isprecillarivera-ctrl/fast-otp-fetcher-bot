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

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 🌟 ━━━━━━ [ GET NUMBER ] ━━━━━━ 🌟 🔥")],
    [KeyboardButton("📢 LIVE OTP"), KeyboardButton("🔒 2FA OPTION")]
], resize_keyboard=True)

async def start(update: Update, context: CallbackContext):
    msg = (
        "╔══════════════════════════════╗\n"
        "      ✨ **SUPER FIRE OTP ENGINE** ✨      \n"
        "╚══════════════════════════════╝\n\n"
        "🚀 **সবচেয়ে দ্রুত এবং প্রফেশনাল ওটিপি সার্ভিসের জন্য প্রস্তুত!**\n\n"
        "📌 **আপনার কাঙ্ক্ষিত অপশনটি সিলেক্ট করুন:**"
    )
    await update.message.reply_text(msg, reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    
    if "GET NUMBER" in text:
        buttons = [
            [InlineKeyboardButton("🔵 FACEBOOK 🔵", callback_data="service_facebook")],
            [InlineKeyboardButton("📸 INSTAGRAM 📸", callback_data="service_instagram")]
        ]
        msg = "👇 **আপনার কাঙ্ক্ষিত সার্ভিসটি সিলেক্ট করুন:**"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)
    
    elif "LIVE OTP" in text:
        msg = (
            "📢 ━━━━━━━━━━━━━━━━━━━━━━ 📢\n"
            "           **📢 LIVE OTP CHANNEL 📢**           \n"
            "📢 ━━━━━━━━━━━━━━━━━━━━━━ 📢\n\n"
            "🔥 **আমাদের এক্সক্লুসিভ গ্রুপে জয়েন করুন** 🔥\n"
            "✅ এখানে রিয়েল-টাইম ওটিপি আপডেট দেখুন।\n\n"
            "👉 [ক্লিক করে জয়েন করুন](https://t.me/SUPERFIREOTP)"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        
    elif "2FA OPTION" in text:
        msg = (
            "🔒 ━━━━━━━━━━━━━━━━━━━━━━ 🔒\n"
            "           **🔒 2FA SECURITY CENTER 🔒**          \n"
            "🔒 ━━━━━━━━━━━━━━━━━━━━━━ 🔒\n\n"
            "🛠 **আমাদের উন্নত সিকিউরিটি ফিচার:**\n"
            "✅ **টু-ফ্যাক্টর বাইপাস সার্ভিস**\n"
            "✅ **প্রফেশনাল একাউন্ট রিকভারি**\n\n"
            "💎 *প্রিমিয়াম সার্ভিসের জন্য সাপোর্টের সাথে যোগাযোগ করুন।* 💎"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

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
            msg = await query.message.reply_text(f"📱 **নম্বর:** `{num}`\n⏳ **ওটিপির জন্য অপেক্ষা করা হচ্ছে...**", parse_mode=ParseMode.MARKDOWN)
            for _ in range(40):
                await asyncio.sleep(7)
                r = await client.post("https://2eee7.com/@Access/@Bot/2eee7/@public/api/getnum", json={"action": "getotp", "id": nid}, headers={"X-API-Key": API_KEY})
                otp = r.json().get("data", {}).get("otp")
                if otp:
                    success_msg = (
                        "✅ **OTP RECEIVED SUCCESSFULLY!** ✅\n\n"
                        f"🔑 **OTP:** `{otp}`\n\n"
                        "🚀 *এটি এখন আপনার গ্রুপে ফরওয়ার্ড করা হয়েছে।* 🚀"
                    )
                    await context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=msg.message_id, text=success_msg, parse_mode=ParseMode.MARKDOWN)
                    await context.bot.send_message(chat_id=GROUP_ID, text=f"🚀 **NEW OTP RECEIVED!**\n\n📱 **Number:** {num}\n🔑 **OTP:** `{otp}`", parse_mode=ParseMode.MARKDOWN)
                    return
            await context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=msg.message_id, text="❌ **দুঃখিত, কোনো ওটিপি পাওয়া যায়নি।**")
        else:
            await query.message.reply_text("❌ এই মুহূর্তে কোনো নম্বর খালি নেই।")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()

if __name__ == '__main__': main()
