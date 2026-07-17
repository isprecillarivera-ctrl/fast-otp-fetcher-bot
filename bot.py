import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE")]
], resize_keyboard=True, persistent=True)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "✅ **SUPER FIRE OTP BOT চালু আছে!**\n\nনিচের বাটনগুলো ব্যবহার করুন।",
        reply_markup=main_keyboard
    )

async def button_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "🎲 GET NUMBER":
        await update.message.reply_text("🔍 GET NUMBER সিলেক্ট হয়েছে।", reply_markup=main_keyboard)
    elif text == "🔐 2FA CODE":
        await update.message.reply_text("🔐 2FA CODE সিলেক্ট হয়েছে।", reply_markup=main_keyboard)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
