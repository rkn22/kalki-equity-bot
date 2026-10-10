from flask import Flask
import threading, os, datetime, random
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_IDS = set()

# 10 Stock Pool - Prati Dina 3 Nua
STOCKS = [
    ["INFY","1680","1665","1710","VWAP Breakout + Volume","3"],
    ["TCS","4050","4020","4110","20EMA Support + RSI 55","1"],
    ["SBIN","800","792","816","BankNifty Momentum + OI","6"],
    ["RELIANCE","2880","2850","2930","Weekly Breakout","2"],
    ["HDFCBANK","1680","1665","1710","Range Breakout","3"],
    ["ICICIBANK","1250","1235","1280","Flag Pattern","4"],
    ["BHARTIARTL","1850","1825","1890","Telecom Momentum","2"],
    ["LT","3600","3550","3680","Construction Bull","1"],
    ["BAJFINANCE","7200","7100","7350","NBFC Support","1"],
    ["MARUTI","12800","12650","13050","Auto Breakout","1"]
]

def get_today_calls():
    random.seed(datetime.date.today().toordinal())
    return random.sample(STOCKS, 3)

# Flask
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "KALKI Dynamic Bot LIVE!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

async def daily_auto(context: ContextTypes.DEFAULT_TYPE):
    calls = get_today_calls()
    msg = "⏰ JAI SHRI KALKI! 9:15 AM\n\n🔥 TODAY'S 3 INTRADAY:\n\n"
    for i, s in enumerate(calls, 1):
        msg += f"{i}. {s[0]} Buy Above {s[1]} | SL {s[2]} | TGT {s[3]}\n Logic: {s[4]}\n Qty: {s[5]} Shares\n\n"
    msg += "Risk: ₹90-120 per trade\nCapital: 15K\n\n📈 SWING: RELIANCE Buy 2880 TGT 3000"
    for cid in list(CHAT_IDS):
        try: await context.bot.send_message(chat_id=cid, text=msg)
        except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("✅ ID Saved! Mon-Fri 9:15 Auto ON!\n\n/today - Nua 3 Calls\n/btst\n/swing")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    calls = get_today_calls()
    msg = "🔥 TODAY'S 3 INTRADAY:\n\n"
    for i, s in enumerate(calls, 1):
        msg += f"{i}. {s[0]} Buy Above {s[1]} | SL {s[2]} | TGT {s[3]}\n Logic: {s[4]}\n Qty: {s[5]} Shares\n\n"
    msg += "Risk: ₹90-120 per trade\nCapital: 15K"
    await update.message.reply_text(msg)

async def btst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌙 BTST:\nCOFORGE @8950 SL 8850 TGT 9150\nM&M @2880 SL 2845 TGT 2935")

async def swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 SWING:\nRELIANCE Buy 2880 TGT 3000\nLT Buy 3600 TGT 3750")

print("KALKI Dynamic Starting...")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("btst", btst))
app.add_handler(CommandHandler("swing", swing))

# Mon-Fri 9:15 AM IST = 03:45 UTC
app.job_queue.run_daily(daily_auto, time=datetime.time(hour=3, minute=45, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4), name="auto_915")

app.run_polling()
