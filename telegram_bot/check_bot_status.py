#!/usr/bin/env python3
import asyncio
import requests

TOKEN = "7640295356:AAEiFqKbAJAZr5EHGuG0q7EcSZ6EZEy0gJA"

def check_bot_status():
    """Проверяем статус бота через API Telegram"""
    print(f"🔍 Проверяем статус бота...")
    print(f"🔑 Токен: {TOKEN[:20]}...")
    
    try:
        # Проверяем информацию о боте
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        print(f"📡 HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                bot_info = data['result']
                print(f"✅ Бот активен!")
                print(f"📱 Имя: {bot_info['first_name']}")
                print(f"🆔 Username: @{bot_info['username']}")
                print(f"🔢 ID: {bot_info['id']}")
                print(f"📝 Может принимать сообщения: {bot_info.get('can_join_groups', 'Неизвестно')}")
                
                # Проверяем webhook
                webhook_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
                webhook_response = requests.get(webhook_url, timeout=10)
                if webhook_response.status_code == 200:
                    webhook_data = webhook_response.json()
                    if webhook_data['ok']:
                        webhook_info = webhook_data['result']
                        webhook_url_set = webhook_info.get('url', '')
                        if webhook_url_set:
                            print(f"⚠️  WEBHOOK установлен: {webhook_url_set}")
                            print(f"❌ Это может блокировать polling!")
                        else:
                            print(f"✅ Webhook не установлен - polling должен работать")
                
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description', 'Неизвестная ошибка')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Тайм-аут соединения")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"💥 Неожиданная ошибка: {e}")
        return False

def remove_webhook():
    """Удаляем webhook если он установлен"""
    print(f"\n🧹 Удаляем webhook...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print(f"✅ Webhook удален!")
                return True
            else:
                print(f"❌ Ошибка удаления webhook: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка при удалении webhook: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Ошибка при удалении webhook: {e}")
        return False

if __name__ == "__main__":
    print(f"🤖 ПРОВЕРКА СТАТУСА TELEGRAM БОТА")
    print(f"=" * 50)
    
    if check_bot_status():
        print(f"\n🔧 Попытка удалить webhook для обеспечения работы polling...")
        remove_webhook()
        print(f"\n🚀 Теперь можно запускать бота через polling!")
        print(f"💡 Используйте: python3 test_kpi_bot.py")
    else:
        print(f"\n❌ Бот недоступен. Проверьте токен.") 