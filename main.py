import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

import feedparser

# === CONFIGURACIÓN ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 480))  # 8 minutos

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

seen_items = set()

FEEDS = [
    "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://apnews.com/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.reuters.com/rss",
    "https://rss.cnn.com/rss/edition_world.rss",
    "https://www.timesofisrael.com/feed/",
    "https://feeds.skynews.com/feeds/rss/world.xml"
]

# === FRASES FUERTES (una sola activa alerta) ===
KEYWORDS_STRONG = [
    "misil balístico", "lanzó misiles", "ataque a israel", "bases estadounidenses",
    "jamenei", "líder supremo", "explosión en teherán", "respuesta iraní",
    "ataque iraní", "misiles iraníes", "bombardeo israelí", "iran ataca",
    "launches ballistic missiles", "attacks israel", "strikes israel", "us bases attacked",
    "khamenei", "supreme leader killed", "explosion in tehran", "iranian missile attack",
    "iran strikes back", "major escalation", "iran retaliation", "israel strikes iran",
    "us strikes iran", "missile barrage", "airstrike on iran", "iranian retaliation",
    "trump orders strike", "persian gulf", "strait of hormuz"
]

# === PALABRAS NORMALES (necesita 3 o más) ===
KEYWORDS = [
    "irán", "iran", "misil", "missile", "ballistic", "ataque", "attack", "strike", "airstrike",
    "israel", "ee.uu.", "usa", "us", "american", "muerto", "killed", "jamenei", "khamenei",
    "ayatollah", "supreme leader", "escalada", "escalation", "hezbolá", "hezbollah", "houthi",
    "teherán", "tehran", "bases", "trump", "netanyahu", "pentagon", "irgc", "revolutionary guard",
    "gulf", "hormuz", "retaliation", "counterattack", "counterstrike", "nuclear", "drone", "idf"
]

async def get_triggering_news(news_list):
    triggering = []
    for entry in news_list:
        text = (entry.title + " " + entry.get('description', '')).lower()
        if any(kw in text for kw in KEYWORDS_STRONG) or sum(1 for kw in KEYWORDS if kw in text) >= 3:
            triggering.append(entry)
    return triggering

async def news_checker():
    await asyncio.sleep(10)
    while True:
        try:
            new_items = []
            for url in FEEDS:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:
                    guid = entry.get("id") or entry.link or entry.title
                    if guid not in seen_items:
                        new_items.append(entry)
                        seen_items.add(guid)

            triggering = await get_triggering_news(new_items)
            if triggering:
                for entry in triggering[:3]:  # máximo 3 alertas por chequeo
                    title = entry.title
                    link = entry.link
                    alert = f"🚨 **ALERTA - EVENTO CLAVE DETECTADO**\n\n**{title}**\n\n{link}\n\nFuente: feeds verificados en tiempo real."
                    await bot.send_message(
                        CHAT_ID, 
                        alert, 
                        parse_mode="Markdown",
                        disable_web_page_preview=False 
                    )

        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

@dp.message(Command("start"))
async def start_cmd(message: Message):
    if message.chat.id == CHAT_ID:
        await message.answer("*Bot de alertas*\n\nCada alerta ahora viene con título + imagen + link directo.", parse_mode="Markdown")

async def main():
    print("Alert Bot iniciado...")
    asyncio.create_task(news_checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
