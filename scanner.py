import yfinance as yf
from datetime import datetime
import os
import requests

stocks = [
    "NVDA","AMD","PLTR","TSLA","SOFI","AAPL",
    "MSFT","GOOGL","META","AMZN","NFLX",
    "AVGO","MU","QCOM","INTC",
    "RIVN","LCID",
    "JPM","BAC","MS","GS",
    "UNH","LLY","JNJ",
    "COIN","SHOP"
]

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

def send_to_discord(message):
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"content": message})

def score_stock(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="6mo")

        if hist.empty or len(hist) < 60:
            return 0

        close = hist["Close"]
        volume = hist["Volume"]

        price = close.iloc[-1]
        if price < 5:
            return 0

        sma50 = close.rolling(50).mean().iloc[-1]
        if str(sma50) == "nan":
            return 0

        avg_volume = volume.rolling(20).mean().iloc[-1]
        today_volume = volume.iloc[-1]
        volume_ratio = today_volume / avg_volume if avg_volume > 0 else 0

        recent_high = close.iloc[-20:].max()
        recent_low = close.iloc[-20:].min()
        range_percent = (recent_high - recent_low) / price

        score = 0

        # Trend
        if price > sma50:
            score += 3
        elif price > sma50 * 0.97:
            score += 2

        # Momentum
        if price > close.iloc[-10]:
            score += 2

        # Breakout pressure
        if price > recent_high * 0.98:
            score += 1

        # Confirmation
        if close.iloc[-1] > close.iloc[-20]:
            score += 1

        # Volume spike
        if volume_ratio >= 1.5:
            score += 2
        elif volume_ratio >= 1.2:
            score += 1

        # Consolidation
        if range_percent < 0.08:
            score += 2
        elif range_percent < 0.12:
            score += 1

        return min(score, 7)

    except:
        return 0


results = []

for s in stocks:
    score = score_stock(s)

    if score == 7:
        label = "BREAKOUT"
    elif score >= 5:
        label = "STRONG"
    elif score >= 3:
        label = "WATCH"
    else:
        label = "WEAK"

    results.append((s, score, label))

results.sort(key=lambda x: x[1], reverse=True)

now = datetime.now().strftime("%Y-%m-%d %H:%M")

# TOP 5 ONLY (clean alerts)
top = results[:5]

output = f"📊 STOCK SCAN ({now})\n\nTOP SETUPS:\n\n"

for r in top:
    output += f"{r[0]}: Score {r[1]} — {r[2]}\n"

print(output)

send_to_discord(output)
