"""
world_intel.py - Live Global News, Finance, and World Monitor Visualizer
Ported & optimized from SAGAR-TAMANG/friday-tony-stark-demo
"""
from __future__ import annotations

import asyncio
import re
import webbrowser
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import httpx

SEED_FEEDS: tuple[str, ...] = (
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
)

FINANCE_SEED_FEEDS: tuple[str, ...] = (
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best",
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
)

_HTML_TAG_RE = re.compile(r"<[^<]+?>")


async def _fetch_and_parse_feed(client: httpx.AsyncClient, url: str) -> list[dict[str, str]]:
    try:
        response = await client.get(url, headers={"User-Agent": "JARVIS-AI/1.0"}, timeout=4.0)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        host = urlparse(url).netloc.replace("www.", "").replace("feeds.", "").replace("rss.", "")
        source_name = host.split(".")[0].upper() if host else "INTEL"

        feed_items: list[dict[str, str]] = []
        for item in root.findall(".//item")[:4]:
            title = (item.findtext("title") or "Unknown").strip()
            description = item.findtext("description") or ""
            if description:
                description = _HTML_TAG_RE.sub("", description).strip()

            feed_items.append({
                "source": source_name,
                "title": title,
                "summary": f"{description[:150]}..." if description else "",
                "link": (item.findtext("link") or "").strip(),
            })
        return feed_items
    except Exception:
        return []


def _fetch_feeds_sync(urls: tuple[str, ...], header: str, empty_msg: str) -> str:
    """Shared concurrent RSS fetcher for World and Financial intelligence."""
    async def _runner() -> list[dict[str, str]]:
        async with httpx.AsyncClient(follow_redirects=True, timeout=6.0) as client:
            results = await asyncio.gather(*(_fetch_and_parse_feed(client, u) for u in urls))
            return [item for sublist in results for item in sublist]

    try:
        articles = asyncio.run(_runner())
    except Exception as e:
        return f"Telemetry feeds are temporarily unresponsive, sir: {e}"

    if not articles:
        return empty_msg

    lines = [header] + [f"- [{art['source']}] {art['title']}" for art in articles[:8]]
    return "\n".join(lines)


def get_world_news_sync() -> str:
    """Synchronous wrapper for parallel world news fetch."""
    return _fetch_feeds_sync(
        SEED_FEEDS,
        "CURRENT GLOBAL HEADLINES:",
        "Global news grid is temporarily unreachable, sir.",
    )


def get_finance_news_sync() -> str:
    """Synchronous wrapper for parallel finance news fetch."""
    return _fetch_feeds_sync(
        FINANCE_SEED_FEEDS,
        "FINANCIAL & MARKET BRIEF:",
        "Financial ticker data is temporarily unavailable, sir.",
    )


def open_world_monitor() -> str:
    """Launch World Monitor interactive radar."""
    webbrowser.open("https://worldmonitor.app/")
    return "Displaying the live World Monitor satellite radar on your primary display now, sir."


def open_finance_monitor() -> str:
    """Launch Finance Monitor interactive dashboard."""
    webbrowser.open("https://finance.worldmonitor.app/")
    return "Displaying the global financial markets dashboard on your primary display, sir."
