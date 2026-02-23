import os
import time
import json
import requests
from datetime import datetime, timezone

# ====== НАСТРОЙКИ ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "ВАШ_ТОКЕН_СЮДА")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@inqnachanachum")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyAzgG8Ax-KOu28AOy89g8KV9wjDfQ9cgow")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")  # заполним ниже
CHECK_INTERVAL = 300  # проверять каждые 5 минут

# Файл для хранения последнего видео
LAST_VIDEO_FILE = "last_video.json"

def get_channel_id():
    """Получить ID канала по имени пользователя"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "id",
        "forHandle": "vardanhakobyan",
        "key": YOUTUBE_API_KEY
    }
    r = requests.get(url, params=params)
    data = r.json()
    if "items" in data and data["items"]:
        return data["items"][0]["id"]
    return None

def get_latest_video(channel_id):
    """Получить последнее видео с канала"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 1,
        "order": "date",
        "type": "video",
        "key": YOUTUBE_API_KEY
    }
    r = requests.get(url, params=params)
    data = r.json()
    if "items" in data and data["items"]:
        item = data["items"][0]
        return {
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "description": item["snippet"]["description"][:200],
            "published": item["snippet"]["publishedAt"],
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
        }
    return None

def load_last_video():
    """Загрузить ID последнего опубликованного видео"""
    try:
        with open(LAST_VIDEO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_last_video(video):
    """Сохранить ID последнего видео"""
    with open(LAST_VIDEO_FILE, "w") as f:
        json.dump(video, f)

def send_to_telegram(video):
    """Отправить видео в Telegram канал"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    text = (
        f"🔴 *Новое видео — Hakobyan News*\n\n"
        f"📺 *{video['title']}*\n\n"
        f"🔗 https://www.youtube.com/watch?v={video['id']}"
    )
    params = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    r = requests.post(url, params=params)
    return r.json()

def main():
    print("🤖 Hakobyan News Bot запущен!")
    
    # Получаем ID канала
    channel_id = YOUTUBE_CHANNEL_ID or get_channel_id()
    if not channel_id:
        print("❌ Не удалось получить ID канала!")
        return
    
    print(f"✅ YouTube канал ID: {channel_id}")
    
    last = load_last_video()
    print(f"📌 Последнее известное видео: {last.get('id', 'нет')}")

    while True:
        try:
            print(f"🔍 Проверяю новые видео... {datetime.now().strftime('%H:%M:%S')}")
            video = get_latest_video(channel_id)
            
            if video:
                if video["id"] != last.get("id"):
                    print(f"🎉 Новое видео: {video['title']}")
                    result = send_to_telegram(video)
                    if result.get("ok"):
                        print("✅ Отправлено в Telegram!")
                        save_last_video(video)
                        last = video
                    else:
                        print(f"❌ Ошибка Telegram: {result}")
                else:
                    print("✓ Новых видео нет")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
