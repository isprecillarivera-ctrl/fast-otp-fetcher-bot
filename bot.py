import logging, re, os, httpx, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("SMS_API_KEY")

UPDATE_CHANNEL = "@SUPERFIREUPDATE"
OTP_CHANNEL = "@SUPERFIREOTP"

# আপনার দেশগুলো
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

async def handle_callback(update, context):
    query = update.callback_query
    data = query.data

    if data == "verify":
        if await is_user_subscribed(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(query.message.chat_id, "স্বাগতম!", reply_markup=main_keyboard)
        else: await query.answer("প্রথমে গ্রুপে জয়েন করুন!", show_alert=True)
    
    # ফেসবুক/ইনস্টাগ্রাম সিলেকশন মেনু
    elif data in ["service_facebook", "service_instagram"]:
        service = data.split("_")[1]
        res = await call_api("liveaccess", method="GET")
        kb = []
        codes = set()
        for s in res.get("services", []):
            if s["sid"].lower() == service.lower():
                for r in s["ranges"]:
                    prefix = re.sub(r'\D', '', str(r))[:3]
                    if prefix in ALLOWED_COUNTRIES: codes.add(prefix)
        for c in codes:
            kb.append([InlineKeyboardButton(f"{ALLOWED_COUNTRIES[c]['flag']} {ALLOWED_COUNTRIES[c]['name']}", callback_data=f"range_{service}_{c}")])
        kb.append([InlineKeyboardButton("🔙 Back", callback_data="back_menu")])
        await query.message.edit_text("Select Country:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("range_"):
        _, service, c_code = data.split("_")
        res = await call_api("liveaccess", method="GET")
        found_range = None
        for s in res.get("services", []):
            if s["sid"].lower() == service.lower():
                for r in s["ranges"]:
                    if str(r).startswith(c_code): found_range = r; break
        
        if found_range:
            msg = await query.message.edit_text("⏳ Allocating...")
            num_res = await call_api("getnum", method="POST", payload={"range": found_range})
            if num_res and num_res.get("meta", {}).get("status") == "ok":
                num_data = num_res["data"]
                await msg.edit_text(f"📱 Number: +{num_data.get('number')}\n⏳ Waiting for OTP...")
                # চেক ওটিপি লজিক
                asyncio.create_task(check_otp(context, query.message.chat_id, num_data["id"], msg.message_id))
    
    elif data == "back_menu":
        await show_platform_menu(query.message)

async def show_platform_menu(msg):
    kb = [[InlineKeyboardButton("🔷 FACEBOOK", callback_data="service_facebook")], [InlineKeyboardButton("📸 INSTAGRAM", callback_data="service_instagram")]]
    await msg.edit_text("Select Platform:", reply_markup=InlineKeyboardMarkup(kb))

async def text_handler(update, context):
    if await is_user_subscribed(context, update.effective_user.id):
        if "GET NUMBER" in update.message.text: await show_platform_menu(update.message)
        else: await update.message.reply_text("মেনু বাটন ব্যবহার করুন।", reply_markup=main_keyboard)
    else:
        # জয়েন বাটন
        kb = [[InlineKeyboardButton("📢 Join Update", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
              [InlineKeyboardButton("📢 Join OTP", url=f"https://t.me/{OTP_CHANNEL.replace('@', '')}")],
              [InlineKeyboardButton("✅ ভেরিফাই", callback_data="verify")]]
        await update.message.reply_text("শুরু করতে জয়েন করুন:", reply_markup=InlineKeyboardMarkup(kb))

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", text_handler))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT, text_handler))
app.run_polling()
