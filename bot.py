import logging, re, os, httpx, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"

# আপনার নির্দিষ্ট ৩টি দেশ
ALLOWED_COUNTRIES = {
    "224": {"name": "Guinea", "flag": "🇬🇳"},
    "232": {"name": "Sierra Leone", "flag": "🇸🇱"},
    "225": {"name": "Ivory Coast", "flag": "🇨🇮"}
}

main_keyboard = ReplyKeyboardMarkup([
    [KeyboardButton("🔥 GET NUMBER 🔥")],
    [KeyboardButton("🔐 2FA CODE"), KeyboardButton("📡 LIVE OTP SECTION")]
], resize_keyboard=True, is_persistent=True)

async def is_user_subscribed(context, user_id):
    try:
        m1 = await context.bot.get_chat_member(chat_id=UPDATE_CHANNEL, user_id=user_id)
        m2 = await context.bot.get_chat_member(chat_id=OTP_CHANNEL, user_id=user_id)
        return m1.status not in ['left', 'kicked'] and m2.status not in ['left', 'kicked']
    except: return False

async def call_api(endpoint, method="POST", payload=None):
    url = f"https://2eee7.com/@Access/@Bot/2eee7/@public/api/{endpoint}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await (client.post(url, json=payload, headers=headers) if method == "POST" else client.get(url, headers=headers))
            return r.json() if r.status_code == 200 else None
        except: return None

async def check_otp(context, chat_id, number_id, msg_id):
    for _ in range(40):
        await asyncio.sleep(5)
        res = await call_api("getotp", method="POST", payload={"action": "getotp", "id": int(number_id)})
        otp = res.get("otp") if res and res.get("otp") else (res.get("data", {}).get("otp") if res else None)
        if otp:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"👑 SUCCESS! OTP: `{otp}`")
            return
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="❌ TIMEOUT")

async def handle_callback(update, context):
    query = update.callback_query
    if query.data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(query.message.chat_id, "স্বাগতম!", reply_markup=main_keyboard)
        else: await query.answer("আপনি গ্রুপে জয়েন করেননি!", show_alert=True)
    
    elif query.data.startswith("range_"):
        _, r_val = query.data.split("_", 1)
        msg = await query.message.edit_text("⚡ Allocating...")
        res = await call_api("getnum", method="POST", payload={"range": r_val})
        if res and res.get("meta", {}).get("status") == "ok":
            num_data = res["data"]
            await msg.edit_text(f"🚀 NUMBER: +{num_data.get('number')}\n⏳ Waiting for OTP...")
            asyncio.create_task(check_otp(context, query.message.chat_id, num_data["id"], msg.message_id))
    
    elif query.data == "get_countries":
        res = await call_api("liveaccess", method="GET")
        kb = []
        # ওয়েবসাইট থেকে আসা লাইভ রেঞ্জ থেকে শুধুমাত্র অনুমোদিত ৩টি দেশ ফিল্টার করা
        for s in res.get("services", []):
            for r in s["ranges"]:
                prefix = re.sub(r'\D', '', str(r))[:3]
                if prefix in ALLOWED_COUNTRIES:
                    kb.append([InlineKeyboardButton(f"{ALLOWED_COUNTRIES[prefix]['flag']} {ALLOWED_COUNTRIES[prefix]['name']}", callback_data=f"range_{r}")])
        await query.message.edit_text("Select Country:", reply_markup=InlineKeyboardMarkup(kb))

async def text_handler(update, context):
    if await is_user_subscribed(context, update.effective_user.id):
        if "GET NUMBER" in update.message.text:
            await update.message.reply_text("Select Country:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌍 Load Live Countries", callback_data="get_countries")]]))
    else:
        # ভেরিফিকেশন বাটন হ্যান্ডলিং
        kb = [[InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
              [InlineKeyboardButton("📢 Join OTP Channel", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
              [InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify")]]
        await update.message.reply_text("ব্যবহার করতে গ্রুপে জয়েন করে ভেরিফাই করুন:", reply_markup=InlineKeyboardMarkup(kb))

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start := lambda u, c: text_handler(u, c)))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT, text_handler))
app.run_polling()
