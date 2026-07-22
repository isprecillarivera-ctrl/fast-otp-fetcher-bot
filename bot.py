import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True)

async def start(update: Update, context):
    await update.message.reply_text(
        "✅ **বট চালু আছে!**\n\n"
        "স্বাগতম! নিচের মেনু থেকে অপশন সিলেক্ট করুন।",
        reply_markup=main_keyboard
    )
    logger.info("Start command worked!")


async def text_handler(update: Update, context):
    text = update.message.text
    if "GET NUMBER" in text:
        await update.message.reply_text("🔢 দেশ সিলেক্ট করুন...")
    elif "LIVE OTP" in text:
        await update.message.reply_text("📡 LIVE OTP সেকশন চালু আছে।")
    else:
        await update.message.reply_text("অপশন সিলেক্ট করুন।")


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("🤖 Bot Started - Test Mode")
    app.run_polling(drop_pending_updates=True)
