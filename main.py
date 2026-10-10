# Same Old Code Upara Same Raha, Tala re Eta Add Kara

WEEKLY_PNL = []
ALERTED = set()

async def live_alert(context: ContextTypes.DEFAULT_TYPE):
    if not TODAY_CALLS: return
    for s in TODAY_CALLS:
        if s[0] in ALERTED: continue
        try:
            df = yf.download(s[0]+".NS", period="1d", interval="1m", progress=False)
            price = float(df['Close'].iloc[-1])
            if price >= s[3]:
                msg = f"🎯 TGT HIT!\n{s[0]} {s[1]} -> {price:.1f}\nProfit: ₹{(price-s[1])*s[5]:.0f}\nBOOK KARO!"
                ALERTED.add(s[0])
            elif price <= s[2]:
                msg = f"🛑 SL HIT!\n{s[0]} {s[1]} -> {price:.1f}\nLoss: ₹{(price-s[1])*s[5]:.0f}\nEXIT KARO!"
                ALERTED.add(s[0])
            else:
                continue
            for cid in list(CHAT_IDS):
                try: await context.bot.send_message(chat_id=cid, text=msg)
                except: pass
        except: pass

async def final_report(context: ContextTypes.DEFAULT_TYPE):
    if not TODAY_CALLS: return
    global WEEKLY_PNL
    msg = f"📊 FINAL REPORT - {datetime.date.today()} 3:30 PM\n\n"
    total = 0
    for s in TODAY_CALLS:
        try:
            df = yf.download(s[0]+".NS", period="1d", interval="5m", progress=False)
            close = float(df['Close'].iloc[-1])
            pnl = (close - s[1]) * s[5]
            total += pnl
            status = "✅ TGT" if close >= s[3] else "❌ SL" if close <= s[2] else "⚠️ CLOSE"
            msg += f"{s[0]}: {s[1]}->{close:.1f} {status} | ₹{pnl:.0f}\n"
        except:
            msg += f"{s[0]}: Data Nahi\n"
    WEEKLY_PNL.append(total)
    msg += f"\n💰 TODAY P&L: ₹{total:.0f}\nJAI SHRI KALKI!"
    for cid in list(CHAT_IDS):
        try: await context.bot.send_message(chat_id=cid, text=msg)
        except: pass

async def weekly_report(context: ContextTypes.DEFAULT_TYPE):
    if not WEEKLY_PNL: return
    total = sum(WEEKLY_PNL)
    msg = f"📈 WEEKLY REPORT\n\n"
    msg += f"Total Trades: {len(WEEKLY_PNL)} Days\n"
    msg += f"Total P&L: ₹{total:.0f}\n"
    msg += f"Avg/Day: ₹{total/len(WEEKLY_PNL):.0f}\n\n"
    msg += "JAI SHRI KALKI! 🙏"
    for cid in list(CHAT_IDS):
        try: await context.bot.send_message(chat_id=cid, text=msg)
        except: pass
    WEEKLY_PNL.clear()

# Job Queue Last re:
# app.job_queue.run_daily(daily_auto, time=datetime.time(hour=3, minute=45, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4))
# app.job_queue.run_daily(final_report, time=datetime.time(hour=10, minute=0, tzinfo=datetime.timezone.utc), days=(0,1,2,3,4))
# app.job_queue.run_repeating(live_alert, interval=300, first=10) # 5 Min
# app.job_queue.run_daily(weekly_report, time=datetime.time(hour=10, minute=30, tzinfo=datetime.timezone.utc), days=(5,)) # Saturday 4 PM
