import os
import time
import requests
import pandas as pd
import otcharts

# Environment variables (set these in Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OTCHARTS_API_KEY = os.getenv("OTCHARTS_API_KEY")

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
    client = otcharts.Client(api_key=OTCHARTS_API_KEY)
    
    # Fetch last 100 candles of M15 EURUSD from the real market book
    # Note: If 'realmarket' gives an error, try 'real_market' or 'forex'
    bars = client.candles("realmarket", "EURUSD", tf=15, limit=100)
    
    # Convert to DataFrame
    df = pd.DataFrame(bars)
    df['close'] = df['close'].astype(float)
    
    # Calculate EMAs
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'])
    
    # Get the last closed candle and the one before it
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    current_price = last_row['close']
    
    # Crossover logic (checking the closed candle vs the one before)
    ema_cross_up = prev_row['ema9'] <= prev_row['ema21'] and last_row['ema9'] > last_row['ema21']
    ema_cross_down = prev_row['ema9'] >= prev_row['ema21'] and last_row['ema9'] < last_row['ema21']
    
    signal = None
    
    if ema_cross_up and last_row['rsi'] > 50:
        signal = (
            f"🟢 *BUY SIGNAL: EURUSD M15*\n\n"
            f"📈 EMA 9 crossed above EMA 21\n"
            f"📊 RSI: {last_row['rsi']:.2f}\n"
            f"💰 Price: {current_price:.5f}\n\n"
            f"🎯 Take Profit: 15 pips\n"
            f"🛑 Stop Loss: 10 pips"
        )
    elif ema_cross_down and last_row['rsi'] < 50:
        signal = (
            f"🔴 *SELL SIGNAL: EURUSD M15*\n\n"
            f"📉 EMA 9 crossed below EMA 21\n"
            f"📊 RSI: {last_row['rsi']:.2f}\n"
            f"💰 Price: {current_price:.5f}\n\n"
            f"🎯 Take Profit: 15 pips\n"
            f"🛑 Stop Loss: 10 pips"
        )
    
    if signal:
        print(f"Sending signal:\n{signal}")
        send_telegram(signal)
    else:
        print(f"No signal. RSI: {last_row['rsi']:.2f}, EMA9: {last_row['ema9']:.5f}, EMA21: {last_row['ema21']:.5f}")

if __name__ == "__main__":
    print("Starting Forex Signal Bot...")
    send_telegram("🤖 Bot is online. Monitoring EURUSD M15...")
    while True:
        try:
            check_market()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(900) # Wait 15 minutes