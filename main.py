import os
import threading
from flask import Flask
import telebot
import yfinance as yf

app = Flask(__name__)
@app.route('/')
def home():
    return "🔱 KALKI Bot Live!"

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

STOCKS = ["TCS.NS","RELIANCE.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS"]

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔱 KALKI Ready!\n/equity - Report")

@bot.message_handler(commands=['equity'])
def equity(m):
    msg = "🔱 *KALKI Equity*\n\n"
    for s in STOCKS:
        try:
            d = yf.download(s, period="2d", progress=False)
            price = float(d['Close'].iloc[-1])
            prev = float(d['Close'].iloc[-2])
            chg = ((price-prev)/prev)*100
            emo = "🟢" if chg>0 else "🔴"
            msg += f"{emo} {s.replace('.NS','')}: {price:.1f} ({chg:+.2f}%)\n"
        except:
            msg += f"{s}: Error\n"
    bot.send_message(m.chat.id, msg, parse_mode="Markdown")

def run_bot():
    print("Bot Polling Started...")
    bot.infinity_polling()

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
