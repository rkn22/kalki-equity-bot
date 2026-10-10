from flask import Flask
import threading, os, datetime, random
import yfinance as yf
import pandas as pd
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_IDS = set()

# Nifty 50 Stocks Check Kariba
NIFTY_50 = ["SBIN.NS","TATASTEEL.NS","RELIANCE.NS","INFY.NS","TCS.NS","ICICIBANK.NS","HDFCBANK.NS","BHEL.NS","TATAPOWER.NS","POWERGRID.NS","NTPC.NS","ITC.NS","TATAMOTORS.NS","FEDERALBNK.NS"]

def analyze_stock(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="15m", progress=False)
        if len(df) < 20: return None
        df['VWAP'] = (df['Close']*df['Volume']).cumsum() / df['Volume'].cumsum()
        df['20EMA'] = df['Close'].ewm(span=20).mean()
        df['VolAvg'] = df['Volume'].rolling(20).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        price = float(last['Close'])
        vwap = float(last['VWAP'])
        ema20 = float(last['20EMA'])
        vol = float(last['Volume'])
        vol_avg = float(last['VolAvg'])

        logic = ""
        signal = False

        if price > vwap and vol > vol_avg*1.5:
            logic = f"VWAP Breakout + Volume {vol/vol_avg:.1f}x"
            signal = True
        elif price > ema20 and last['Close'] > prev['Close']:
            logic = f"20EMA Support + Bullish"
            signal = True
        elif vol > vol_avg*2:
            logic = f"High Volume Breakout {vol/vol_avg:.1f}x"
            signal = True

        if signal:
            sl = round(price * 0.99, 1)
            tgt = round(price * 1.02, 1)
            qty = int(15000 // price)
            return [symbol.replace(".NS",""), round(price,1), sl, tgt, logic, qty]
    except:
        return None
    return None

def get_live_top3():
    top = []
    random.shuffle(NIFTY_50)
    for sym in NIFTY_50[:10]: # Speed Pain 10 Ta Check
        res = analyze_stock(sym)
        if res:
            top.append(res)
        if len(top) == 3:
            break
    if len(top) < 3: # Fallback
        return [
            ["SBIN",800,792,816,"Fallback: Bank Momentum","18"],
            ["TATASTEEL",165,162,171,"Fallback: Metal Breakout","90"],
            ["POWERGRID",310,304,320,"Fallback: Power Support","48"]
        ]
    return top

# Flask
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "KALKI LIVE ANALYZER ON!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("⏳ Live Exchange Check Karuchi... 10 Sec")
    calls = get_live_top3()
    msg = f"🔥 LIVE TOP 3 - {datetime.date.today()}:\nNSE Analysis:\n\n"
    for i, s in enumerate(calls, 1):
        msg += f"{i}. {s[0]} Buy Above {s[1]} | SL {s[2]} | TGT {s[3]}\n Logic: {s[4]}\n Qty: {s[5]} | Cap: 15K\n\n"
    await update.message.reply_text(msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    CHAT_IDS.add(update.effective_chat.id)
    await update.message.reply_text("✅ Live Analyzer ON! /today Daba")

print("Live Analyzer Starting...")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
# Auto 9:15 AM
app.job_queue.run_daily(lambda c: c.bot.send_message, time=datetime.time(hour=3, minute=45, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4))

# Custom auto with analysis
async def daily_auto(context: ContextTypes.DEFAULT_TYPE):
    calls = get_live_top3()
    msg = f"⏰ JAI SHRI KALKI! 9:15 AM LIVE SCAN\n\n🔥 TOP 3 TODAY:\n\n"
    for i, s in enumerate(calls, 1):
        msg += f"{i}. {s[0]} Buy {s[1]} SL {s[2]} TGT {s[3]}\n {s[4]} Qty {s[5]}\n\n"
    for cid in list(CHAT_IDS):
        try: await context.bot.send_message(chat_id=cid, text=msg)
        except: pass

app.job_queue.run_daily(daily_auto, time=datetime.time(hour=3, minute=45, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4))

app.run_polling()
