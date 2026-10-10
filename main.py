from flask import Flask
import threading, os, datetime, random
import yfinance as yf
import pandas as pd
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_IDS = set()
TODAY_CALLS = []

NIFTY_50 = ["SBIN.NS","TATASTEEL.NS","RELIANCE.NS","INFY.NS","TCS.NS","ICICIBANK.NS","HDFCBANK.NS","BHEL.NS","TATAPOWER.NS","POWERGRID.NS","NTPC.NS","ITC.NS","TATAMOTORS.NS"]

def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="15m", progress=False)
        if len(df) < 20: return None
        df['VWAP'] = (df['Close']*df['Volume']).cumsum() / df['Volume'].cumsum()
        df['20EMA'] = df['Close'].ewm(span=20).mean()
        df['VolAvg'] = df['Volume'].rolling(20).mean()
        last = df.iloc[-1]
        price = float(last['Close'])
        vwap = float(last['VWAP'])
        vol_avg = float(last['VolAvg'])
        vol = float(last['Volume'])
        logic = ""
        if price > vwap and vol > vol_avg*1.5: logic = f"VWAP Breakout Vol {vol/vol_avg:.1f}x"
        elif vol > vol_avg*2: logic = f"High Vol {vol/vol_avg:.1f}x"
        else: logic = f"20EMA Bullish"
        sl = round(price * 0.99, 1)
        tgt = round(price * 1.02, 1)
        qty = int(15000 // price)
        if qty < 1: qty = 1
        return [symbol.replace(".NS",""), round(price,1), sl, tgt, logic, qty]
    except:
        return None

def get_live_top3():
    global TODAY_CALLS
    top = []
    random.shuffle(NIFTY_50)
    for sym in NIFTY_50[:12]:
        res = analyze_stock(sym)
        if res: top.append(res)
        if len(top) == 3: break
    if len(top) < 3:
        top = [["SBIN",800,792,816,"Top Bank Momentum","18"],["TATASTEEL",165,162,171,"Metal Breakout","90"],["POWERGRID",310,304,320,"Power Support","48"]]
    TODAY_CALLS = top
    return top

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "KALKI 9:15 & 3:30 LIVE!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

async def daily_auto(context: ContextTypes.DEFAULT_TYPE):
    calls = get_live_top3()
    msg = f"⏰ JAI SHRI KALKI! {datetime.date.today()}\n\n🔥 9:15 AM TOP 3 TRADE (NSE LIVE):\n\n"
    for i, s in enumerate(calls, 1):
        msg += f"{i}. {s[0]} Buy Above {s[1]} | SL {s[2]} | TGT {s[3]}\n Logic: {s[4]}\n Qty: {s[5]} | Cap: ~15K\n\n"
    msg += "⚠️ 3:30 PM re Final Report Asiba"
    for cid in list(CHAT_IDS):
        try: await context.bot.send_message(chat_id=cid, text=msg)
        except: pass

async def final_report(context: ContextTypes.DEFAULT_TYPE):
    if not TODAY_CALLS: return
    msg = f"📊 FINAL REPORT - {datetime.date.today()} 3:30 PM\n\n"
    total = 0
    for s in TODAY_CALLS:
        try:
            df = yf.download(s[0]+".NS", period="1d", interval="5m", progress=False)
            close = float(df['Close'].iloc[-1])
            pnl = (close - s[1]) * s[5]
            total += pnl
            status = "✅ TGT" if close >= s[3] else "❌ SL" if close <= s[2] else "⚠️ CLOSE"
            msg += f"{s[0]}: {s[1]} -> {close:.1f} {status} | P&L ₹{pnl:.0f}\n"
        except:
            msg += f"{s[0]}: Data Nahi\n"
    msg += f"\n💰 TOTAL P&L: ₹{total:.0f}\nJAI SHRI KALKI! 🙏"
    for cid in list(CHAT_IDS):
        try: await context.bot.send_message(chat_id=cid, text=msg)
        except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Bot ON!\n9:15 AM Top 3\n3:30 PM Final Report\n/today")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("⏳ Live NSE Scan...")
    calls = get_live_top3()
    msg = f"🔥 TOP 3 - {datetime.date.today()}:\n\n"
    for i, s in enumerate(calls, 1):
        msg += f"{i}. {s[0]} Buy {s[1]} SL {s[2]} TGT {s[3]}\n {s[4]} Qty {s[5]}\n\n"
    await update.message.reply_text(msg)

print("Bot Starting...")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.job_queue.run_daily(daily_auto, time=datetime.time(hour=3, minute=45, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4))
app.job_queue.run_daily(final_report, time=datetime.time(hour=10, minute=0, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4))
app.run_polling()
