from flask import Flask
import threading, os, datetime, pytz
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_IDS = set()

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "KALKI Auto Bot LIVE Mon-Fri 9:15!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

async def daily_auto(context: ContextTypes.DEFAULT_TYPE):
    msg = """⏰ JAI SHRI KALKI! 9:15 AM Market Open!
    
🔥 TODAY'S 3 INTRADAY CALLS (Research Based):

1. INFY - Buy Above 1680 | SL 1665 | TGT 1710
   Qty: 3 | Logic: VWAP Breakout

2. TCS - Buy Above 4050 | SL 4020 | TGT 4110
   Qty: 1 | Logic: 20EMA Support

3. SBIN - Buy Above 800 | SL 792 | TGT 816
   Qty: 6 | Logic: Bank Momentum

📈 SWING BONUS: RELIANCE Buy 2880 | TGT 3000

Manual: /today /btst /swing /research TCS /risk"""

    for cid in list(CHAT_IDS):
        try: await context.bot.send_message(chat_id=cid, text=msg)
        except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text(f"✅ ID Saved: {update.effective_chat.id}\n\nMon-Fri 9:15 AM Auto Alert ON!\n\n/today - 3 Calls\n/btst - BTST\n/swing - Swing\n/research INFY - Live Research\n/risk - Calculator\n\nManual Message Dele Bi Asiba!")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("🔥 TODAY'S 3 INTRADAY:\n\n1. INFY Buy Above 1680 | SL 1665 | TGT 1710\n2. TCS Buy Above 4050 | SL 4020 | TGT 4110\n3. SBIN Buy Above 800 | SL 792 | TGT 816\n\nRisk: ₹90-120 per trade")

async def btst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌙 BTST:\nCOFORGE @8950 SL 8850 TGT 9150\nM&M @2880 SL 2845 TGT 2935")

async def swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 SWING (2-5 Days):\nRELIANCE Buy 2880 TGT 3000\nLT Buy 3600 TGT 3750")

print("Bot Starting Mon-Fri 9:15...")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("btst", btst))
app.add_handler(CommandHandler("swing", swing))

# Mon=0 ... Fri=4, 9:15 AM IST = 3:45 AM UTC
app.job_queue.run_daily(daily_auto, time=datetime.time(hour=3, minute=45, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4), name="auto_915")

app.run_polling()
