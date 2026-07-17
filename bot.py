import logging
import re
import os
import requests
import pyotp
from datetime import datetime
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

OTP_PATTERN = re.compile(r'\b(\d{4,8})\b')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 💎 সুপার-ক্লিন ও প্রফেশনাল কিবোর্ড (ব্যালেন্স ছাড়া শুধু কাজের অপশন)
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")]
], resize_keyboard=True, is_persistent=True)

# 🌍 গ্লোবাল লাইভ রেঞ্জ টু কান্ট্রি ম্যাপার
def get_flag_and_name(code_str):
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
        "380": ("Ukraine", "🇺🇦"),
        "92":  ("Pakistan", "🇵🇰"),
        "20":  ("Egypt", "🇪🇬")
    }
    for prefix, info in country_map.items():
        if code_str.startswith(prefix):
            return info
    return ("International Server", "🌍")

async def start(update: Update, context: CallbackContext):
    if not update.message:
        return
    name = update.effective_user.first_name
    
    # আল্ট্রা-লাক্সারি নিওন স্টাইলড ওয়েলকাম স্ক্রিন (টাকা-পয়সার কোনো লেখা নেই)
    await update.message.reply_text(
        f"✨ **WELCOME TO SUPER FIRE OTP ENGINE** ✨\n"
        f"📥 `User:` **{name}**\n"
        f"⚡ `System:` **Premium Multi-Route Active**\n"
        f"═══════════════════════\n"
        f"🤖 *Select an option from the menu below to begin:*",
        reply_markup=main_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

# 🔄 ডাইনামিক লাইভ রেঞ্জ মেনু
async def show_ranges_menu(message_obj, service_name="Facebook"):
    live_ranges = ["26134", "224655", "23274"] 
    
    buttons = []
    for r in live_ranges:
        c_name, c_flag = get_flag_and_name(r)
        buttons.append([InlineKeyboardButton(f"📡 {c_flag} {c_name} ({r})", callback_data=f"select_{service_name.lower()}_{r}")])
    
    buttons.append([InlineKeyboardButton("🔄 ⚡ REFRESH RANGES ⚡ 🔄", callback_data=f"refresh_{service_name.lower()}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await message_obj.reply_text(
        f"🔥 **LIVE ACTIVE RANGES FOR {service_name.upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *সিলেক্ট করুন কোন দেশের নাম্বার প্রয়োজন:*",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data

    if data == "refresh_facebook":
        await query.message.delete()
        await show_ranges_menu(query.message, "Facebook")

    elif data.startswith("select_"):
        parts = data.split("_")
        service = parts[1]
        selected_range = parts[2]
        
        c_name, c_flag = get_flag_and_name(selected_range)
        generated_number = f"{selected_range}{datetime.now().strftime('%M%S%f')[:6]}"
        
        # 💎 লাক্সারি ট্যাপ-টু-কপি ইনলাইন লেআউট
        number_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📋 🔗 +{generated_number} (Tap to Copy)", callback_data=f"copy_{generated_number}")],
            [InlineKeyboardButton("🔄 Change Number", callback_data=f"select_{service}_{selected_range}")],
            [InlineKeyboardButton("🌐 Change Country Range", callback_data="refresh_facebook")]
        ])
        
        await query.message.delete()
        await query.message.reply_text(
            f"⚡ **NUMBER SUCCESSFULLY ASSIGNED** ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 `Region:` **{c_flag} {c_name}**\n"
            f"⏱️ `Status:` **Waiting for Dynamic OTP...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 *নাম্বার কপি করতে নিচের বাটনে চাপ দিন:*",
            reply_markup=number_buttons,
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif data.startswith("copy_"):
        num = data.split("_")[1]
        await query.answer(text=f"✅ +{num} Copied to Clipboard!", show_alert=True)

async def handle_message(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return
    text = update.message.text

    if text == "🎲 GET NUMBER":
        await show_ranges_menu(update.message, "Facebook")
        
    elif text == "🔐 2FA CODE":
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
    
    print("🚀 DYNAMIC ENGINE LIVE (NO BALANCE MODE)...")
    app.run_polling()

if __name__ == '__main__':
    main()
