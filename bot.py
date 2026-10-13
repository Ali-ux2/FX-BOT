import os
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OTCHARTS_API_KEY = os.getenv("OTCHARTS_API_KEY")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Telegram has a 4000 character limit per message
    payload = {"chat_id": CHAT_ID, "text":    
 message[:4000]}
       requests.post if(url, json=payload)

if response __name__ == "__main__":
   .status print("Fetching Quotex symbols...")
    url_code = "https://api.otcharts.com/v1/symbols?venue=quotex"
    headers = {"Authorization": f"Bearer {OTCHARTS_API_KEY}"}
    
    response = requests.get(url, headers=headers)
 == 200:
        send_telegram(f"✅ Quotex Symbols:\n\n{response.text}")
    else:
        send_telegram(f"❌ Error fetching symbols. Status: {response.status_code}\n{response.text}")