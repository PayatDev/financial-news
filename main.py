import os
import re
import requests
import feedparser
from datetime import datetime

# === Config ===
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# === ข่าวไทย ===
def fetch_thai_news():
    sources = [
        ("kaohoon", "https://www.kaohoon.com/feed"),
        ("prachachat", "https://www.prachachat.net/feed"),
        ("infoquest", "https://www.infoquest.co.th/feed"),
        ("finnomena", "https://www.finnomena.com/feed/"),
    ]
    articles = []
    for name, url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:7]:
                summary = re.sub('<.*?>', '', entry.get("summary", ""))[:300]
                articles.append(f"[{name}] {entry.title}: {summary}")
        except Exception as e:
            print(f"⚠️ {name}: {e}")
    return "\n\n".join(articles)

# === ข่าวโลก ===
def fetch_world_news():
    sources = [
        ("zerohedge", "https://feeds.feedburner.com/zerohedge/feed"),
        ("investing", "https://www.investing.com/rss/news_25.rss"),
    ]
    articles = []
    for name, url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:7]:
                summary = re.sub('<.*?>', '', entry.get("summary", ""))[:300]
                articles.append(f"[{name}] {entry.title}: {summary}")
        except Exception as e:
            print(f"⚠️ {name}: {e}")
    return "\n\n".join(articles)

# === Claude สรุป ===
def summarize(thai_news, world_news):
    prompt = f"""ข่าวไทยวันนี้:
{thai_news}

ข่าวต่างประเทศวันนี้:
{world_news}

สรุปเป็นภาษาไทย แบบเพื่อนซุบซิบให้กันฟัง โดย:
- เลือกข่าวสำคัญสุด 5 ข่าวไทย และ 5 ข่าวโลก เท่านั้น
- ทุกครั้งที่พูดถึงหุ้น บอก ชื่อเต็มบริษัท / ทำธุรกิจอะไร
- แต่ละข่าว 2-3 ประโยค กระชับ ได้ใจความ
- แบ่ง 🇹🇭 หุ้นไทย และ 🌍 ต่างประเทศ
- ลงท้าย 📌 สรุปภาพรวม 1 ประโยค
- ห้ามเกิน 3000 ตัวอักษรรวมทั้งหมด"""

    res = requests.post("https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return res.json()["content"][0]["text"]

# === ส่ง Telegram ===
def send_telegram(text):
    date_str = datetime.now().strftime("%d/%m/%Y")
    full = f"📰 *ข่าวหุ้นประจำวัน {date_str}*\n\n{text}"
    chunks = [full[i:i+4000] for i in range(0, len(full), 4000)]
    for chunk in chunks:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        )
    print(f"✅ ส่งแล้ว {len(chunks)} ข้อความ")

# === Main ===
if __name__ == "__main__":
    print("📡 ดึงข่าว...")
    thai = fetch_thai_news()
    world = fetch_world_news()
    print(f"ไทย: {len(thai.splitlines())} บรรทัด | โลก: {len(world.splitlines())} บรรทัด")

    print("🤖 Claude สรุป...")
    summary = summarize(thai, world)
    print(f"ความยาว: {len(summary)} ตัวอักษร")

    print("📨 ส่ง Telegram...")
    send_telegram(summary)
