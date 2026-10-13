import os
import time
import requests
import pandas as pd
import otcharts

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OTCHARTS_API_KEY = os.getenv("OTCHARTS_API_KEY")

# Major Pairs for this bot (No slashes, matches Quotex format)
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def check_market():
    # Initialize OTCharts client
    client = otcharts.Client(api_key=OTCHARTS_API_KEY)
    
    for pair in PAIRS:
        try:
            # Fetch M5 data from Quotex book
            bars = client.candles("quotex", pair, tf=5, limit=100)
            
            if not bars:
                print(f"No data received for {pair} on Quotex.")
                continue

            df = pd.DataFrame(bars)
            df['close'] = df['close'].astype(float)
            
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['rsi'] = calculate_rsi(df['close'])
            
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            current_price = last_row['close']
            
            ema_cross_up = prev_row['ema9'] <= prev_row['ema21'] and last_row['ema9'] > last_row['ema21']
            ema_cross_down = prev_row['ema9'] >= prev_row['ema21'] and last_row['ema9'] < last_row['ema21']
            
            signal = None
            
            if ema_cross_up and last_row['rsi'] > 50:
                signal = (
                    f"🟢 *BUY SIGNAL: {pair} M5 (Quotex)*\n\n"
                    f"📈 EMA 9 crossed above EMA 21\n"
                    f"📊 RSI: {last_row['rsi']:.2f}\n"
                    f"💰 Price: {current_price:.5f}\n\n"
                    f"🎯 Take Profit: 15 pips\n"
                    f"🛑 Stop Loss: 10 pips\n\n"
                    f"⚠️ *Verify on Exness MT5 before entering!*"
                )
            elif ema_cross_down and last_row['rsi'] < 50:
                signal = (
                    f"🔴 *SELL SIGNAL: {pair} M5 (Quotex)*\n\n"
                    f"📉 EMA 9 crossed below EMA 21\n"
                    f"📊 RSI: {last_row['rsi']:.2f}\n"
                    f"💰 Price: {current_price:.5f}\n\n"
                    f"🎯 Take Profit: 15 pips\n"
                    f"🛑 Stop Loss: 10 pips\n\n"
                    f"⚠️ *Verify on Exness MT5 before entering!*"
                )
            
            if signal:
                print(f"Sending signal for {pair}")
                send_telegram(signal)
            else:
                print(f"No signal for {pair}. RSI: {last_row['rsi']:.2f}")
            
            time.sleep(1) # Delay to avoid hitting API limits
            
        except Exception as e:
            print(f"Error checking {pair}: {e}")

if __name__ == "__main__":
    print("Starting Forex Signal Bot (Quotex Major Pairs)...")
    send_telegram("🤖 *Major Pairs Bot* is online. Monitoring EURUSD, GBPUSD, USDJPY on M5...\n⚠️ Remember to verify on Exness MT5 before trading!")
    while True:
        try:
            check_market()
        except Exception as e:
            print(f"Main Loop Error: {e}")
        time.sleep(300) # Wait 5 minutes (300 seconds) for M5