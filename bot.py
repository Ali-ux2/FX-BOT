import os
import time
import requests
import pandas as pd
import otcharts

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OTCHARTS_API_KEY = os.getenv("OTCHARTS_API_KEY")

# Quotex format uses _otc suffix
PAIRS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"]

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
    
    for pair in PAIRS:
        try:
            # Fetch M5 data (Quotex does not support M1)
            bars = client.candles("quotex", pair, tf=5, limit=100)
            
            if not bars:
                print(f"No data received for {pair}.")
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
            
            # OPEN BUY SIGNAL
            if ema_cross_up and last_row['rsi'] > 50:
                signal = (
                    f"🟢 *OPEN BUY: {pair} M5*\n\n"
                    f"📈 EMA 9 crossed above EMA 21\n"
                    f"📊 RSI: {last_row['rsi']:.2f}\n"
                    f"💰 Price: {current_price:.5f}\n\n"
                    f"🎯 Take Profit: 10 pips\n"
                    f"🛑 Stop Loss: 5 pips"
                )
            # OPEN SELL SIGNAL
            elif ema_cross_down and last_row['rsi'] < 50:
                signal = (
                    f"🔴 *OPEN SELL: {pair} M5*\n\n"
                    f"📉 EMA 9 crossed below EMA 21\n"
                    f"📊 RSI: {last_row['rsi']:.2f}\n"
                    f"💰 Price: {current_price:.5f}\n\n"
                    f"🎯 Take Profit: 10 pips\n"
                    f"🛑 Stop Loss: 5 pips"
                )
            # CLOSE SIGNAL (Opposite Cross)
            elif ema_cross_up and last_row['rsi'] < 50:
                signal = (
                    f"⚠️ *CLOSE SELL TRADE: {pair} M5*\n\n"
                    f"🔄 EMA 9 crossed above EMA 21\n"
                    f"📊 RSI: {last_row['rsi']:.2f}\n"
                    f"💰 Price: {current_price:.5f}\n\n"
                    f"➡️ *Close any open SELL positions on this pair.*"
                )
            elif ema_cross_down and last_row['rsi'] > 50:
                signal = (
                    f"⚠️ *CLOSE BUY TRADE: {pair} M5*\n\n"
                    f"🔄 EMA 9 crossed below EMA 21\n"
                    f"📊 RSI: {last_row['rsi']:.2f}\n"
                    f"💰 Price: {current_price:.5f}\n\n"
                    f"➡️ *Close any open BUY positions on this pair.*"
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
    print("Starting M5 Scalping Bot...")
    send_telegram("🤖 *M5 Scalping Bot* is online. Monitoring EURUSD, GBPUSD, USDJPY on M5...")
    while True:
        try:
            check_market()
        except Exception as e:
            print(f"Main Loop Error: {e}")
        time.sleep(300) # Wait 5 minutes for M5