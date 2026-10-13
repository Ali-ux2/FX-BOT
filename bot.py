import os
from otcharts import Client

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message[:4000]}
    requests.post(url, json=payload)

if __name__ == "__main__":
    print("Fetching Quotex symbols...")
    try:
        otc = Client()
        symbols = list(otc.symbols("quotex"))
        
        if not symbols:
            send_telegram("❌ No symbols returned. Your plan might not open the Quotex book.")
        else:
            # Build a readable list of symbol IDs
            lines = [f"{s.symbol} | {s.name}" for s in symbols]
            message = "✅ Quotex symbols your key can read:\n\n" + "\n".join(lines)
            send_telegram(message)
            print(f"Found {len(symbols)} symbols.")
            
    except Exception as e:
        error_msg = f"❌ Error: {type(e).__name__} - {e}"
        print(error_msg)
        send_telegram(error_msg)
