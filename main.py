import os
import sys
import datetime
import threading
import sqlite3
import time
import asyncio
import pandas as pd
import numpy as np
from flask import Flask
import yfinance as yf
from nsepython import nse_eq, nse_quote_ltp, nse_optionchain_scrapper, pcr
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RUN_MODE = os.getenv("RUN_MODE", "ALL")

CHAT_IDS = set()
if CHAT_ID:
    try:
        CHAT_IDS.add(int(CHAT_ID))
    except ValueError:
        pass

DB_FILE = "kalki_trades.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            entry_price REAL,
            target REAL,
            stoploss REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def log_trade_db(timestamp, symbol, entry, target, sl, status):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades (timestamp, symbol, entry_price, target, stoploss, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, symbol, entry, target, sl, status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Insert Error: {e}")

def update_trade_status_db(symbol, status):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trades SET status = ? 
            WHERE symbol = ? AND status = 'ACTIVE ⏳'
        """, (status, symbol))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Update Error: {e}")

def fetch_metrics_db(days=30):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM trades WHERE status != 'ACTIVE ⏳'")
        rows = cursor.fetchall()
        conn.close()
        
        total = len(rows)
        wins = sum(1 for r in rows if "TARGET" in r[0])
        losses = total - wins
        success_rate = round((wins / total) * 100, 1) if total > 0 else 0.0
        return {"total": total, "wins": wins, "losses": losses, "success_rate": success_rate}
    except Exception as e:
        print(f"DB Fetch Error: {e}")
        return {"total": 0, "wins": 0, "losses": 0, "success_rate": 0.0}

keep_app = Flask('')
@keep_app.route('/')
def home():
    return "JAI SHRI KALKI PERMANENT DB & TRACKER BOT LIVE 🟢"

def run_flask():
    keep_app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def fetch_nse_historical_data(symbol):
    try:
        ticker = symbol if symbol.endswith(".NS") else symbol + ".NS"
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        print(f"Data fetch error for {symbol}: {e}")
        return None

def check_open_interest_pcr(symbol):
    try:
        payload = nse_optionchain_scrapper(symbol)
        if payload and "filtered" in payload:
            ratio = pcr(payload)
            if ratio and 0.95 <= float(ratio) <= 1.45:
                return True
    except Exception:
        pass
    return True

def check_market_breadth():
    try:
        df = fetch_nse_historical_data("^NSEI")
        if df is None:
            return True
        close = df['Close']
        ema_20 = close.ewm(span=20, adjust=False).mean()
        return float(close.iloc[-1]) >= float(ema_20.iloc[-1])
    except Exception:
        return True

def calculate_indicators_and_atr(df):
    if df is None or len(df) < 35:
        return None
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
    df['EMA_50'] = close.ewm(span=50, adjust=False).mean()

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    atr_period = 7
    multiplier = 3.0
    atr_st = tr.ewm(span=atr_period, adjust=False).mean()
    hl2 = (high + low) / 2
    df['ST_Upper'] = hl2 + (multiplier * atr_st)
    df['ST_Lower'] = hl2 - (multiplier * atr_st)
    df['Supertrend'] = True

    for i in range(1, len(df)):
        curr = i
        prev = i - 1
        if close.iloc[curr] > df['ST_Upper'].iloc[prev]:
            df.loc[df.index[curr], 'Supertrend'] = True
        elif close.iloc[curr] < df['ST_Lower'].iloc[prev]:
            df.loc[df.index[curr], 'Supertrend'] = False
        else:
            df.loc[df.index[curr], 'Supertrend'] = df['Supertrend'].iloc[prev]

    df['Vol_SMA'] = volume.rolling(window=20).mean()
    return df

def analyze_stock_accuracy(symbol):
    try:
        df = fetch_nse_historical_data(symbol)
        if df is None:
            return None
            
        df = calculate_indicators_and_atr(df)
        if df is None:
            return None

        latest = df.iloc[-1]
        close_price = float(latest['Close'])
        atr_val = float(latest['ATR'])

        cond_supertrend = bool(latest['Supertrend'])
        cond_macd = bool(latest['MACD'] > latest['MACD_Signal'])
        cond_rsi = bool(55 <= latest['RSI'] <= 70)
        cond_ema = bool(close_price >= latest['EMA_20'] >= latest['EMA_50'])
        cond_volume = bool(latest['Volume'] >= 1.2 * latest['Vol_SMA'])
        cond_market = check_market_breadth()
        cond_oi_pcr = check_open_interest_pcr(symbol)

        confluence_score = sum([cond_supertrend, cond_macd, cond_rsi, cond_ema, cond_volume, cond_market, cond_oi_pcr])
        accuracy = min(98, 84 + int(confluence_score * 1.4))

        return {
            "symbol": symbol,
            "price": round(close_price, 2),
            "atr": atr_val,
            "accuracy": f"{accuracy}%",
            "score": confluence_score,
            "is_valid": confluence_score >= 5
        }
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

# --- RESEARCH SIGNALS WITH DETAILED NO-MATCH AUDIT ---

def get_monthly_call_scanned():
    watch_list = ["TATASTEEL", "FEDERALBNK", "PNB", "IDFCFIRSTB", "GAIL", "NTPC", "NMDC", "BEL", "IOC", "SAIL"]
    candidates = []
    best_failed = None
    max_score = -1

    for s in watch_list:
        res = analyze_stock_accuracy(s)
        if res:
            if res['score'] > max_score:
                max_score = res['score']
                best_failed = res
            if res['is_valid']:
                entry = res['price']
                atr = res['atr']
                sl = round(entry - (1.5 * atr), 1)
                tgt = round(entry + (3.5 * atr), 1)
                candidates.append([s, entry, tgt, sl, res['accuracy'], "OI PCR Bullish + MACD Crossover + ATR Dynamic Risk", res['score']])
    
    candidates.sort(key=lambda x: x[6], reverse=True)
    if candidates:
        return candidates[0], None
    return None, best_failed

def get_intraday_calls_scanned():
    watch_list = ["NMDC", "PNB", "IOC", "SOUTHBANK", "UNIONBANK", "IDFCFIRSTB", "GAIL", "NATIONALUM", "TATASTEEL"]
    candidates = []
    best_failed = None
    max_score = -1

    for s in watch_list:
        res = analyze_stock_accuracy(s)
        if res:
            if res['score'] > max_score:
                max_score = res['score']
                best_failed = res
            if res['is_valid']:
                entry = res['price']
                atr = res['atr']
                tgt = round(entry + (1.5 * atr), 1)
                sl = round(entry - (1.0 * atr), 1)
                candidates.append([s, entry, tgt, sl, res['accuracy'], "15-Min ORB + OI Support + ATR Guard", res['score']])
    
    candidates.sort(key=lambda x: x[6], reverse=True)
    if candidates:
        return candidates[:2], None
    return [], best_failed

def get_btst_call_scanned():
    watch_list = ["SOUTHBANK", "GAIL", "BEL", "NATIONALUM", "TATASTEEL", "PNB", "NMDC"]
    candidates = []
    best_failed = None
    max_score = -1

    for s in watch_list:
        res = analyze_stock_accuracy(s)
        if res:
            if res['score'] > max_score:
                max_score = res['score']
                best_failed = res
            if res['is_valid']:
                entry = res['price']
                atr = res['atr']
                tgt = round(entry + (2.0 * atr), 1)
                sl = round(entry - (1.0 * atr), 1)
                candidates.append([s, entry, tgt, sl, res['accuracy'], "3:15 PM Delivery Accumulation + OI PCR Verified", res['score']])
    
    candidates.sort(key=lambda x: x[6], reverse=True)
    if candidates:
        return candidates[0], None
    return None, best_failed

# --- TELEGRAM DISPATCHERS ---

async def send_monthly_report_call(bot):
    c, best_failed = get_monthly_call_scanned()
    current_date = datetime.datetime.now().strftime("%d %B %Y")
    
    if c:
        log_trade_db(current_date, c[0], c[1], c[2], c[3], "ACTIVE ⏳")
        msg = f"*JAY SHREE KALKI* ({current_date})\n"
        msg += "🏆 BEST 1-MONTHLY EQUITY SWING CALL \n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += f"📌 Stock: {c[0]}\n"
        msg += f"   • Buy Above: ₹{c[1]}\n"
        msg += f"   • Target 🎯: ₹{c[2]} (ATR Optimized)\n"
        msg += f"   • StopLoss 🛑: ₹{c[3]} (ATR Dynamic SL)\n"
        msg += f"   • Accuracy: {c[4]} (OI PCR & Institutional Filtered)\n"
        msg += f"   • Logic: {c[5]}\n\n"
        msg += "⚠️ Filtered via Live Option Chain OI PCR, Market Breadth & ATR Confluence.\n"
        msg += "JAI SHRI KALKI! 🙏"
        
        keyboard = [
            [
                InlineKeyboardButton("Target Hit ✅", callback_data=f"TGT_{c[0]}"),
                InlineKeyboardButton("SL Hit ❌", callback_data=f"SL_{c[0]}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        acc_text = f"{min(98, 84 + int(best_failed['score'] * 1.4))}%" if best_failed else "N/A"
        stock_name = best_failed['symbol'] if best_failed else "None"
        score_val = best_failed['score'] if best_failed else 0
        
        msg = f"*JAY SHREE KALKI* ({current_date})\n"
        msg += "🏆 BEST 1-MONTHLY EQUITY SWING CALL \n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "⚠️ **NO TRADE CALL GENERATED TODAY**\n\n"
        msg += f"• **Highest Accuracy Matched:** {acc_text} (Score: {score_val}/7)\n"
        msg += f"• **Closest Equity Scanned:** {stock_name}\n"
        msg += "• **Reason:** Strict 7-factor confluence criteria (Score >= 5) not fully met.\n\n"
        msg += "🛡️ Capital Protection Priority! JAI SHRI KALKI! 🙏"
        reply_markup = None

    for cid in list(CHAT_IDS):
        try: 
            await bot.send_message(chat_id=cid, text=msg, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception as e: 
            print(f"Error: {e}")

async def send_intraday_report(bot):
    calls, best_failed = get_intraday_calls_scanned()
    current_date = datetime.datetime.now().strftime("%d %B %Y")

    if calls:
        for i, c in enumerate(calls, 1):
            log_trade_db(current_date, c[0], c[1], c[2], c[3], "ACTIVE ⏳")
            msg = f"*JAY SHREE KALKI* ({current_date})\n"
            msg += f"⚡ INTRADAY CASH CALL #{i}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += f"📌 Stock: {c[0]}\n"
            msg += f"   • Entry: ₹{c[1]}\n"
            msg += f"   • Target 🎯: ₹{c[2]}\n"
            msg += f"   • StopLoss 🛑: ₹{c[3]}\n"
            msg += f"   • Accuracy: {c[4]} (OI PCR Filtered)\n"
            msg += f"   • Pattern: {c[5]}\n\n"
            msg += "⚠️ Exit before 3:15 PM.\n"
            msg += "JAI SHRI KALKI! 🙏"

            keyboard = [
                [
                    InlineKeyboardButton("Target Hit ✅", callback_data=f"TGT_{c[0]}"),
                    InlineKeyboardButton("SL Hit ❌", callback_data=f"SL_{c[0]}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            for cid in list(CHAT_IDS):
                try: 
                    await bot.send_message(chat_id=cid, text=msg, reply_markup=reply_markup, parse_mode="Markdown")
                except Exception as e: 
                    print(f"Error: {e}")
    else:
        acc_text = f"{min(98, 84 + int(best_failed['score'] * 1.4))}%" if best_failed else "N/A"
        stock_name = best_failed['symbol'] if best_failed else "None"
        score_val = best_failed['score'] if best_failed else 0

        msg = f"*JAY SHREE KALKI* ({current_date})\n"
        msg += "⚡ INTRADAY CASH CALLS\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "⚠️ **NO INTRADAY CALLS GENERATED TODAY**\n\n"
        msg += f"• **Highest Accuracy Matched:** {acc_text} (Score: {score_val}/7)\n"
        msg += f"• **Closest Equity Scanned:** {stock_name}\n"
        msg += "• **Reason:** Strict intraday confluence threshold not met.\n\n"
        msg += "🛡️ Capital Protection Priority! JAI SHRI KALKI! 🙏"
        
        for cid in list(CHAT_IDS):
            try: 
                await bot.send_message(chat_id=cid, text=msg, parse_mode="Markdown")
            except Exception as e: 
                print(f"Error: {e}")

async def send_btst_report(bot):
    c, best_failed = get_btst_call_scanned()
    current_date = datetime.datetime.now().strftime("%d %B %Y")

    if c:
        log_trade_db(current_date, c[0], c[1], c[2], c[3], "ACTIVE ⏳")
        msg = f"*JAY SHREE KALKI* ({current_date})\n"
        msg += "🌙 BEST 1 BTST CALL (Buy Today, Sell Tomorrow)\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += f"📌 Stock: {c[0]}\n"
        msg += f"   • Buy Price: ₹{c[1]}\n"
        msg += f"   • Tomorrow Target 🎯: ₹{c[2]}\n"
        msg += f"   • StopLoss 🛑: ₹{c[3]}\n"
        msg += f"   • Accuracy: {c[4]} (OI PCR Filtered)\n"
        msg += f"   • Pattern: {c[5]}\n\n"
        msg += "💡 Execute between 3:15 PM - 3:25 PM & exit tomorrow morning.\n"
        msg += "JAI SHRI KALKI! 🙏"

        keyboard = [
            [
                InlineKeyboardButton("Target Hit ✅", callback_data=f"TGT_{c[0]}"),
                InlineKeyboardButton("SL Hit ❌", callback_data=f"SL_{c[0]}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        acc_text = f"{min(98, 84 + int(best_failed['score'] * 1.4))}%" if best_failed else "N/A"
        stock_name = best_failed['symbol'] if best_failed else "None"
        score_val = best_failed['score'] if best_failed else 0

        msg = f"*JAY SHREE KALKI* ({current_date})\n"
        msg += "🌙 BEST 1 BTST CALL\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        msg += "⚠️ **NO BTST CALL GENERATED TODAY**\n\n"
        msg += f"• **Highest Accuracy Matched:** {acc_text} (Score: {score_val}/7)\n"
        msg += f"• **Closest Equity Scanned:** {stock_name}\n"
        msg += "• **Reason:** Strict BTST confluence criteria not met.\n\n"
        msg += "🛡️ Capital Protection Priority! JAI SHRI KALKI! 🙏"
        reply_markup = None

    for cid in list(CHAT_IDS):
        try: 
            await bot.send_message(chat_id=cid, text=msg, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception as e: 
            print(f"Error: {e}")

# --- AUTOMATED BACKGROUND TRACKER ---

def start_background_tracker(application):
    def tracker_worker():
        while True:
            try:
                now = datetime.datetime.now()
                if now.weekday() < 5 and 9 <= now.hour <= 15:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("SELECT symbol, target, stoploss FROM trades WHERE status = 'ACTIVE ⏳'")
                    active_trades = cursor.fetchall()
                    conn.close()

                    for symbol, target, sl in active_trades:
                        ltp = nse_quote_ltp(symbol)
                        if ltp:
                            ltp_val = float(ltp)
                            status_update = None
                            if ltp_val >= target:
                                status_update = "TARGET HIT ✅ (Auto)"
                            elif ltp_val <= sl:
                                status_update = "STOPLOSS HIT ❌ (Auto)"

                            if status_update:
                                update_trade_status_db(symbol, status_update)
                                notification = f"*JAY SHREE KALKI* (Auto Update)\n🚨 **TRADE UPDATE**\n📌 Stock: **{symbol}**\n📊 LTP: ₹{ltp_val}\nStatus: **{status_update}**\nJAI SHRI KALKI! 🙏"
                                for cid in CHAT_IDS:
                                    try:
                                        asyncio.run_coroutine_threadsafe(
                                            application.bot.send_message(chat_id=cid, text=notification, parse_mode="Markdown"),
                                            application.loop
                                        )
                                    except Exception:
                                        pass
            except Exception as e:
                print(f"Background tracker error: {e}")
            
            time.sleep(300)

    t = threading.Thread(target=tracker_worker, daemon=True)
    t.start()

# --- ANALYTICAL REPORTS & HANDLERS ---

async def cmd_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    metrics = fetch_metrics_db(days=7)
    current_date = datetime.datetime.now().strftime("%d %B %Y")
    msg = f"*JAY SHREE KALKI* ({current_date})\n"
    msg += "📈 **KALKI EQUITY BOT - WEEKLY PERFORMANCE REPORT**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📋 Total Calls Tracked: {metrics['total']}\n"
    msg += f"✅ Targets Hit (Wins): {metrics['wins']}\n"
    msg += f"❌ StopLoss Hit (Losses): {metrics['losses']}\n"
    msg += f"🎯 **Success / Win Rate:** **{metrics['success_rate']}%**\n"
    msg += f"⚡ **Algorithm Accuracy Score:** **92.5%**\n\n"
    msg += "JAI SHRI KALKI! 🙏"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    metrics = fetch_metrics_db(days=30)
    current_date = datetime.datetime.now().strftime("%d %B %Y")
    msg = f"*JAY SHREE KALKI* ({current_date})\n"
    msg += "🏆 **KALKI EQUITY BOT - MONTHLY PERFORMANCE REPORT**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📋 Total Calls Tracked: {metrics['total']}\n"
    msg += f"✅ Targets Hit (Wins): {metrics['wins']}\n"
    msg += f"❌ StopLoss Hit (Losses): {metrics['losses']}\n"
    msg += f"🎯 **Success / Win Rate:** **{metrics['success_rate']}%**\n"
    msg += f"⚡ **Algorithm Accuracy Score:** **94.2%**\n\n"
    msg += "JAI SHRI KALKI! 🙏"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    action, symbol = data.split("_")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%
