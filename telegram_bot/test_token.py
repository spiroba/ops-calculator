import os
from dotenv import load_dotenv
import requests

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')

print(f"Testing token: {token}")

# Проверяем токен через API
url = f"https://api.telegram.org/bot{token}/getMe"
response = requests.get(url)

print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    if data.get('ok'):
        bot_info = data.get('result', {})
        print(f"✅ Bot is valid!")
        print(f"Bot name: {bot_info.get('first_name')}")
        print(f"Bot username: @{bot_info.get('username')}")
    else:
        print("❌ Bot API returned error:", data.get('description'))
else:
    print("❌ HTTP error:", response.status_code) 