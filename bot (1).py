import os
import time
import json
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ====== НАСТРОЙКИ ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@inqnachanachum")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
CHECK_INTERVAL = 300  # проверять каждые 5 минут
LAST_VIDEO_FILE = "last_video.json"

# Простой веб-сервер чтобы Render не останавливал бота
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hakobyan News Bot is running!")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), PingHandler)
    server.serve_forever()

def get_channel_id():
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "id", "forHandle": "vardanhakobyan", "key": YOUTUBE_API_KEY}
    r = requests.get(url, params=params)
    data = r.json()
    if "items" in data and data["items"]:
        return data["items"][0]["id"]
    return None

def get_latest_video(channel_id):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet", "channelId": channel_id,
        "maxResults": 1, "order": "date", "type": "video", "key": YOUTUBE_API_KEY
    }
    r = requests.get(url, params=params)
    data = r.json()
    if "items" in data and data["items"]:
        item = data["items"][0]
        return {
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
        }
    return None

def load_last_video():
    try:
        with open(LAST_VIDEO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_last_video(video):
    with open(LAST_VIDEO_FILE, "w") as f:
        json.dump(video, f)

def send_to_telegram(video):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    text = (
        f"🔴 *Новое видео — Hakobyan News*\n\n"
        f"📺 *{video['title']}*\n\n"
        f"🔗 https://www.youtube.com/watch?v={video['id']}"
    )
    params = {"chat_id": TELEGRAM_CHANNEL, "text": text, "parse_mode": "Markdown"}
    r = requests.post(url, params=params)
    return r.json()

def bot_loop():
    print("🤖 Hakobyan News Bot запущен!")
    channel_id = get_channel_id()
    if not channel_id:
        print("❌ Не удалось получить ID канала!")
        return
    print(f"✅ YouTube канал ID: {channel_id}")
    last = load_last_video()

    while True:
        try:
            print(f"🔍 Проверяю... {time.strftime('%H:%M:%S')}")
            video = get_latest_video(channel_id)
            if video and video["id"] != last.get("id"):
                print(f"🎉 Новое видео: {video['title']}")
                result = send_to_telegram(video)
                if result.get("ok"):
                    print("✅ Отправлено в Telegram!")
                    save_last_video(video)
                    last = video
                else:
                    print(f"❌ Ошибка: {result}")
            else:
                print("✓ Новых видео нет")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    # Запускаем бота
    bot_loop()
