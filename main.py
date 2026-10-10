from flask import Flask
import threading, os, datetime
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_IDS = set()

# Flask for Render
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "KALKI Bot LIVE - Mon-Fri 9:15 Auto!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

# Auto Daily Message Mon-Fri 9:15 AM
async def daily_auto(context: ContextTypes.DEFAULT_TYPE):
    msg = """⏰ JAI SHRI KALKI! 9:15 AM Market Open!

🔥 TODAY'S 3 INTRADAY:

1. INFY Buy Above 1680 | SL 1665 | TGT 1710
   Logic: VWAP Breakout + Volume
   Qty: 3 Shares

2. TCS Buy Above 4050 | SL 4020 | TGT 4110
   Logic: 20EMA Support + RSI 55
   Qty: 1 Share

3. SBIN Buy Above 800 | SL 792 | TGT 816
   Logic: BankNifty Momentum + Open Interest
   Qty: 6 Shares

Risk: ₹90-120 per trade
Capital: 15K

📈 SWING: RELIANCE Buy 2880 | TGT 3000"""

    for cid in list(CHAT_IDS):
        try:
            await context.bot.send_message(chat_id=cid, text=msg)
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("✅ ID Saved!\n\nMon-Fri 9:15 AM Auto ON!\n\n/today - Intraday\n/btst - BTST\n/swing - Swing")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    msg = """🔥 TODAY'S 3 INTRADAY:

1. INFY Buy Above 1680 | SL 1665 | TGT 1710
   Logic: VWAP Breakout + Volume
   Qty: 3 Shares

2. TCS Buy Above 4050 | SL 4020 | TGT 4110
   Logic: 20EMA Support + RSI 55
   Qty: 1 Share

3. SBIN Buy Above 800 | SL 792 | TGT 816
   Logic: BankNifty Momentum + Open Interest
   Qty: 6 Shares

Risk: ₹90-120 per trade
Capital: 15K"""
    await update.message.reply_text(msg)

async def btst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌙 BTST:\nCOFORGE @8950 SL 8850 TGT 9150\nM&M @2880 SL 2845 TGT 2935")

async def swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 SWING:\nRELIANCE Buy 2880 TGT 3000\nLT Buy 3600 TGT 3750")

# Start Bot
print("KALKI Bot Starting...")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("btst", btst))
app.add_handler(CommandHandler("swing", swing))

# Mon-Fri 9:15 AM IST = 3:45 AM UTC, days=(0,1,2,3,4)
app.job_queue.run_daily(daily_auto, time=datetime.time(hour=3, minute=45, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4), name="auto_915")

app.run_polling()
