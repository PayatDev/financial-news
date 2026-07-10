import os
import re
import requests
import feedparser
from datetime import datetime

# === Config ===
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# === Sources แต่ละหมวด ===
SOURCES = {
    "🧠 Behavior": [
        "https://www.businessinsider.com/rss",
        "https://www.vox.com/rss/money/index.xml",
        "https://www.theatlantic.com/feed/all/",
    ],
    "🌍 Macro": [
        "https://www.marctomarket.com/feeds/posts/default",
        "https://blogs.imf.org/feed/",
        "https://www.project-syndicate.org/rss",
    ],
    "📊 Investment Strategy": [
        "https://alphaarchitect.com/feed/",
        "https://awealthofcommonsense.com/feed/",
        "https://www.artemis.bm/feed/",
    ],
    "💰 Personal Finance": [
        "https://www.kitces.com/blog/feed/",
        "https://www.financialplanningassociation.org/rss.xml",
        "https://retirementresearcher.com/feed/",
    ],
    "🤖 Technology": [
        "https://www.fintechfutures.com/feed/",
        "https://www.finextra.com/rss/headlines.aspx",
        "https://feeds.feedburner.com/TechCrunch/",
    ],
    "🎯 เรื่องน่าสนใจ": [
        "https://www.noahpinion.blog/feed",
        "https://feeds.feedburner.com/zerohedge/feed",
        "https://www.economist.com/finance-and-economics/rss.xml",
    ],
    "🌏 Geopolitics": [
        "https://www.cfr.org/rss/economics",
        "https://www.project-syndicate.org/rss",
        "https://moderndiplomacy.eu/feed/",
    ],
}

# === ดึงข่าวแต่ละหมวด ===
def fetch_articles(urls, max_per_source=5):
    articles = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_source]:
                title = entry.title
                summary = re.sub('<.*?>', '', entry.get("summary", ""))[:400]
                articles.append(f"- {title}: {summary}")
        except Exception as e:
            print(f"⚠️ {url}: {e}")
    return "\n\n".join(articles)

# === Claude เลือกและ rewrite ===
def pick_and_rewrite(category, articles):
    prompt = f"""หมวด: {category}

บทความที่ดึงมาได้:
{articles}

จากบทความข้างต้น:
1. เลือก 1 บทความที่น่าสนใจที่สุด เหมาะกับนักลงทุนและคนสนใจการเงิน
2. Rewrite เป็นภาษาไทย เล่าเป็นเรื่องราว ไม่เป็นทางการ อ่านสนุก
3. ความยาว 4-5 ประโยค มีตัวเลขหรือข้อมูลจริงประกอบ
4. ขึ้นต้นด้วยชื่อเรื่องสั้นๆ ที่น่าสนใจ
5. ห้ามเกิน 400 ตัวอักษร"""

    res = requests.post("https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return res.json()["content"][0]["text"]

# === ส่ง Telegram ===
def send_telegram(text):
    date_str = datetime.now().strftime("%d/%m/%Y")
    full = f"📚 *บทความการเงินประจำวัน {date_str}*\n\n{text}"
    chunks = [full[i:i+4000] for i in range(0, len(full), 4000)]
    for chunk in chunks:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        )
    print(f"✅ ส่งแล้ว {len(chunks)} ข้อความ")

# === Main ===
if __name__ == "__main__":
    all_content = ""

    for category, urls in SOURCES.items():
        print(f"📡 ดึง {category}...")
        articles = fetch_articles(urls)
        if not articles:
            print(f"⚠️ ไม่มีข้อมูล {category}")
            continue
        print(f"🤖 Claude สรุป {category}...")
        content = pick_and_rewrite(category, articles)
        all_content += f"{category}\n{content}\n\n{'─'*30}\n\n"

    print("📨 ส่ง Telegram...")
    send_telegram(all_content)
