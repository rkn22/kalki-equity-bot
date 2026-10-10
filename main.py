import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Jai Shree Kalki! Bot Live ✅")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Price Feature Asiba...")

if __name__ == "__main__":
    print("KALKI Bot Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    print("KALKI Bot Started...")
    app.run_polling()
