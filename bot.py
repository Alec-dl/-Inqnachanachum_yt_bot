import os,time,json,requests,threading
from http.server import HTTPServer,BaseHTTPRequestHandler

TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN","")
TELEGRAM_CHANNEL=os.getenv("TELEGRAM_CHANNEL","@inqnachanachum")
YOUTUBE_API_KEY=os.getenv("YOUTUBE_API_KEY","")
CHECK_INTERVAL=300
LAST_VIDEO_FILE="last_video.json"

class PingHandler(BaseHTTPRequestHandler):
 def do_GET(self):
  self.send_response(200);self.end_headers();self.wfile.write(b"Bot running!")
 def log_message(self,f,*a):pass

def get_channel_id():
 r=requests.get("https://www.googleapis.com/youtube/v3/channels",params={"part":"id","forHandle":"vardanhakobyan","key":YOUTUBE_API_KEY})
 d=r.json();return d["items"][0]["id"] if "items" in d and d["items"] else None

def get_latest_video(cid):
 r=requests.get("https://www.googleapis.com/youtube/v3/search",params={"part":"snippet","channelId":cid,"maxResults":1,"order":"date","type":"video","key":YOUTUBE_API_KEY})
 d=r.json()
 if "items" in d and d["items"]:
  i=d["items"][0];return{"id":i["id"]["videoId"],"title":i["snippet"]["title"]}

def load_last():
 try:
  with open(LAST_VIDEO_FILE) as f:return json.load(f)
 except:return{}

def save_last(v):
 with open(LAST_VIDEO_FILE,"w") as f:json.dump(v,f)

def send_tg(v):
 requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",params={"chat_id":TELEGRAM_CHANNEL,"text":f"🔴 Новое видео\n\n{v['title']}\n\nhttps://youtu.be/{v['id']}"})

def bot_loop():
 print("Bot started!")
 cid=get_channel_id()
 if not cid:print("No channel!");return
 print(f"Channel: {cid}");last=load_last()
 while True:
  try:
   v=get_latest_video(cid)
   if v and v["id"]!=last.get("id"):
    send_tg(v);save_last(v);last=v;print(f"Sent: {v['title']}")
   else:print("No new videos")
  except Exception as e:print(f"Error: {e}")
  time.sleep(CHECK_INTERVAL)

port=int(os.getenv("PORT",8080))
server=HTTPServer(("0.0.0.0",port),PingHandler)
print(f"Server on port {port}")
threading.Thread(target=bot_loop,daemon=True).start()
server.serve_forever()
