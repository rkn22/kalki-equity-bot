from flask import Flask
import threading
import os
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Fake Web Server for Render Free Plan
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "KALKI Bot Running Successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# Telegram Bot Code
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Jai Shri Kalki! Bot is Live! 🚀")

print("KALKI Bot Starting...")
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
