import asyncio
import feedparser
from bs4 import BeautifulSoup as _BS
import httpx as _httpx
from core.config import GRACE_PROXY, logger
from services.ai import summarize_intel_report, clean_ai_arabic_text

def normalize_url(url: str) -> str:
    """Normalize a URL to prevent duplicates while preserving essential query parameters."""
    if not url: return ""
    try:
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
        url = url.strip().rstrip('/')
        parsed = urlparse(url)
        if parsed.query:
            tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'fbclid', 'gclid', 'ref'}
            query_params = parse_qsl(parsed.query, keep_blank_values=True)
            filtered_params = [(k, v) for k, v in query_params if k.lower() not in tracking_params]
            new_query = urlencode(filtered_params)
            parsed = parsed._replace(query=new_query)
            url = urlunparse(parsed)
    except: pass
    return url.lower()

async def fetch_article_content(url: str) -> str:
    """Scrapes the full text content of an article URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with _httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200: return ""
            soup = _BS(resp.text, 'html.parser')
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            article = soup.find('article') or soup.find(class_='post-content') or soup.body
            if not article: return ""
            paragraphs = article.find_all('p')
            text = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return text[:8000]
    except Exception as e:
        logger.warning(f"Error scraping article {url}: {e}")
        return ""

async def fetch_news(sector=None, limit_per_source=1):
    """Fetch news from all sources with cross-source deduplication."""
    # Logic will use a helper to get sources
    # This is a placeholder for now to ensure structure is correct
    pass
