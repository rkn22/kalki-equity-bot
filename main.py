import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Jai Shree Kalki! Bot Live Achhi ✅\n/price INFY - Price dekhba pain")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        import yfinance as yf
        if not context.args:
            await update.message.reply_text("Ex: /price INFY")
            return
        symbol = context.args[0].upper()
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")
        if data.empty:
            await update.message.reply_text(f"{symbol} Data Miluni")
            return
        price = round(data['Close'].iloc[-1], 2)
        await update.message.reply_text(f"📈 {symbol}: Rs {price}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not found!")
        exit(1)
    print("KALKI Bot Started...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.run_polling()
