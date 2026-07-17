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

# 💎 ভিআইপি ডার্ক-নিওন মেইন কিবোর্ড লেআউট
main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")],
    [KeyboardButton("💰 BALANCE"), KeyboardButton("💳 WITHDRAWAL")],
    [KeyboardButton("📩 CONTACT ADMIN")]
], resize_keyboard=True, is_persistent=True)

# 🌍 গ্লোবাল রেঞ্জ টু কান্ট্রি ফাস্ট ট্র্যাকার
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
    
    # লাক্সারি স্টাইলড ওয়েলকাম স্ক্রিন
    await update.message.reply_text(
        f"✨ **WELCOME TO THE FUTURE OF OTP** ✨\n"
        f"📥 `User:` **{name}**\n"
        f"⚡ `Status:` **High-Speed Operational**\n"
        f"═══════════════════════\n"
        f"💰 **Available Balance:** `0.0 BDT`\n"
        f"═══════════════════════\n"
        f"🤖 *Select a dynamic engine option below:*",
        reply_markup=main_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

async def show_ranges_menu(message_obj, service_name="Facebook"):
    # এপিআই রেঞ্জ ডেমো ডেটা
    live_ranges = ["26134", "224655", "23274"] 
    
    buttons = []
    for r in live_ranges:
        c_name, c_flag = get_flag_and_name(r)
        # প্রিমিয়াম বাটন টেক্সট ফরম্যাটিং
        buttons.append([InlineKeyboardButton(f"📡 {c_flag} {c_name} [{r}]", callback_data=f"select_{service_name.lower()}_{r}")])
    
    # কালার ব্যালেন্সড কন্ট্রোল বাটন
    buttons.append([InlineKeyboardButton("🔄 ⚡ QUICK REFRESH ⚡ 🔄", callback_data=f"refresh_{service_name.lower()}")])
    buttons.append([InlineKeyboardButton("🔙 Back to Services", callback_data="back_services")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await message_obj.reply_text(
        f"🔥 **LIVE ACTIVE RANGES FOR {service_name.upper()}**\n"
        f"📱 `Engine:` Dynamic Multi-Route\n"
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

    if data == "back_services" or data == "refresh_facebook":
        await query.message.delete()
        await show_ranges_menu(query.message, "Facebook")

    elif data.startswith("select_"):
        parts = data.split("_")
        service = parts[1]
        selected_range = parts[2]
        
        c_name, c_flag = get_flag_and_name(selected_range)
        generated_number = f"{selected_range}{datetime.now().strftime('%M%S%f')[:6]}"
        
        # 💎 সম্পূর্ণ কাস্টম এবং মেটালিক-স্টাইল ইনলাইন লেআউট
        number_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📋 🔗 Click to Copy: +{generated_number}", callback_data=f"copy_{generated_number}")],
            [InlineKeyboardButton("🔄 Request Another Number", callback_data=f"select_{service}_{selected_range}")],
            [InlineKeyboardButton("🌍 Swap Country Range", callback_data="back_services")],
            [InlineKeyboardButton("📢 JOIN LIVE OTP CHAT 🔗", url="https://t.me/your_otp_group")]
        ])
        
        await query.message.delete()
        await query.message.reply_text(
            f"⚡ **NUMBER SUCCESSFULLY ASSIGNED** ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 `Region:` **{c_flag} {c_name}**\n"
            f"🏷️ `Rate:` **0.5 BDT / Per SMS**\n"
            f"⏱️ `Status:` **Waiting for Secure OTP...**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 *নিচের বাটনে ট্যাপ করলেই নাম্বারটি কপি হয়ে যাবে:*",
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
        
    elif text == "💰 BALANCE":
        await update.message.reply_text(
            "💳 **VIP ACCOUNT WALLET**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 `Current Balance:` **0.0 BDT**\n"
            f"⚡ `Tier Status:` **Premium User**",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif text == "💳 WITHDRAWAL":
        await update.message.reply_text(
            "💸 **WITHDRAWAL INSTANT GATEWAY**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ `Notice:` **Minimum withdrawal limit is 100 BDT.**",
            parse_mode=ParseMode.MARKDOWN
        )
        
    elif text == "📩 CONTACT ADMIN":
        await update.message.reply_text(
            "🛠️ **VIP CLIENT SUPPORT**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 কোনো সমস্যা বা বাল্ক অর্ডারের জন্য সরাসরি এডমিনকে মেসেজ দিন:\n"
            "➡️ **@Easymarketingsupport**",
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
    
    print("🚀 ULTRA-PREMIUM BOT ENGINE DEPLOYED...")
    app.run_polling()

if __name__ == '__main__':
    main()
