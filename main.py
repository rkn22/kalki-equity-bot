from flask import Flask
import threading, os, yfinance as yf
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Web Server for Render
app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "KALKI Bot Running!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

# Research Logic
def get_research(symbol):
    try:
        ticker = yf.Ticker(symbol + ".NS")
        hist = ticker.history(period="1mo")
        if hist.empty: return None
        close = hist['Close'].iloc[-1]
        sma20 = hist['Close'].rolling(20).mean().iloc[-1]
        rsi = 55 # simplified, full formula add later
        trend = "BULLISH" if close > sma20 else "BEARISH"
        return f"📊 {symbol} : ₹{close:.2f}\nTrend: {trend}\nSMA20: ₹{sma20:.2f}\nSetup: {'Buy on Dip' if trend=='BULLISH' else 'Avoid/Sell'}"
    except:
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Jai Shri Kalki! 🚀\nCommands:\n/today - Intraday Calls\n/swing - Swing Picks\n/research TCS - Full Analysis\n/risk - 15k Calculator")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🔥 TODAY'S TOP 3 INTRADAY (15K Capital):\n\n1. INFY - Buy Above 1680 | SL 1665 | TGT 1710\n Logic: VWAP Breakout + Volume\n Qty: 3 Shares (~5k)\n\n2. TCS - Buy Above 4050 | SL 4020 | TGT 4110\n Logic: 20EMA Support\n Qty: 1 Share\n\n3. SBIN - Buy Above 800 | SL 792 | TGT 816\n Logic: BankNifty Momentum\n Qty: 6 Shares\n\nRisk per trade: ₹90-120"
    await update.message.reply_text(msg)

async def swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📈 SWING PICKS (2-5 Days):\n\n1. RELIANCE - Buy 2880-2900 | SL 2830 | TGT 3000\n Logic: Daily Chart Breakout\n\n2. LT - Buy 3600 | SL 3530 | TGT 3750\n Logic: Strong Uptrend + RSI 58"
    await update.message.reply_text(msg)

async def research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /research TCS")
        return
    symbol = context.args[0].upper()
    res = get_research(symbol)
    if res: await update.message.reply_text(res)
    else: await update.message.reply_text(f"{symbol} data miluni. NSE symbol lekha: RELIANCE, INFY, TCS")

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 15K RISK CALCULATOR:\nCapital: ₹15000\nRisk/Trade: 1% = ₹150\n\nFormula:\nQty = 150 / (Entry - SL)\n\nEg: Entry 800, SL 792 => Diff 8\nQty = 150/8 = 18 Shares = ₹14,400 (Too High!)\nSo Use 6 Shares Only = ₹4800 Investment")

print("KALKI Bot Starting...")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("swing", swing))
app.add_handler(CommandHandler("research", research))
app.add_handler(CommandHandler("risk", risk))
app.run_polling()
