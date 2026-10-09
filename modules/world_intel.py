"""
world_intel.py - Live Global News, Finance, and World Monitor Visualizer
Ported & optimized from SAGAR-TAMANG/friday-tony-stark-demo
"""

import httpx
import xml.etree.ElementTree as ET
import asyncio
import re
import webbrowser

SEED_FEEDS = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://www.cnbc.com/id/100727362/device/rss/rss.html',
    'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    'https://www.aljazeera.com/xml/rss/all.xml'
]

FINANCE_SEED_FEEDS = [
    'https://www.cnbc.com/id/10000664/device/rss/rss.html',
    'https://feeds.bloomberg.com/markets/news.rss',
    'https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best',
    'https://feeds.marketwatch.com/marketwatch/topstories/',
    'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',
]

async def _fetch_and_parse_feed(client, url):
    try:
        response = await client.get(url, headers={'User-Agent': 'JARVIS-AI/1.0'}, timeout=4.0)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        source_name = url.split('.')[1].upper() if '.' in url else 'INTEL'
        
        feed_items = []
        items = root.findall(".//item")[:4]
        for item in items:
            title = item.findtext("title")
            description = item.findtext("description")
            link = item.findtext("link")
            
            if description:
                description = re.sub('<[^<]+?>', '', description).strip()

            feed_items.append({
                "source": source_name,
                "title": title or "Unknown",
                "summary": (description[:150] + "...") if description else "",
                "link": link or ""
            })
        return feed_items
    except Exception:
        return []

def get_world_news_sync() -> str:
    """Synchronous wrapper for parallel world news fetch."""
    async def _runner():
        async with httpx.AsyncClient(follow_redirects=True, timeout=6.0) as client:
            tasks = [_fetch_and_parse_feed(client, url) for url in SEED_FEEDS]
            results = await asyncio.gather(*tasks)
            all_articles = [item for sublist in results for item in sublist]
            return all_articles

    try:
        loop = asyncio.new_event_loop()
        articles = loop.run_until_complete(_runner())
        loop.close()
    except Exception as e:
        return f"Satellite telemetry indicates feeds are unresponsive right now, sir: {e}"

    if not articles:
        return "Global news grid is temporarily unreachable, sir."

    brief = ["CURRENT GLOBAL HEADLINES:"]
    for art in articles[:8]:
        brief.append(f"- [{art['source']}] {art['title']}")
    return "\n".join(brief)

def get_finance_news_sync() -> str:
    """Synchronous wrapper for parallel finance news fetch."""
    async def _runner():
        async with httpx.AsyncClient(follow_redirects=True, timeout=6.0) as client:
            tasks = [_fetch_and_parse_feed(client, url) for url in FINANCE_SEED_FEEDS]
            results = await asyncio.gather(*tasks)
            all_articles = [item for sublist in results for item in sublist]
            return all_articles

    try:
        loop = asyncio.new_event_loop()
        articles = loop.run_until_complete(_runner())
        loop.close()
    except Exception as e:
        return f"Market feeds are currently unresponsive, sir: {e}"

    if not articles:
        return "Financial ticker data is temporarily unavailable, sir."

    brief = ["FINANCIAL & MARKET BRIEF:"]
    for art in articles[:8]:
        brief.append(f"- [{art['source']}] {art['title']}")
    return "\n".join(brief)

def open_world_monitor() -> str:
    """Launch World Monitor interactive radar."""
    webbrowser.open("https://worldmonitor.app/")
    return "Displaying the live World Monitor satellite radar on your primary display now, sir."

def open_finance_monitor() -> str:
    """Launch Finance Monitor interactive dashboard."""
    webbrowser.open("https://finance.worldmonitor.app/")
    return "Displaying the global financial markets dashboard on your primary display, sir."
