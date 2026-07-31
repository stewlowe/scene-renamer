import httpx
from selectolax.parser import HTMLParser
from typing import List, Optional
from urllib.parse import quote
from .models import SceneCandidate
from config import DATA18_BASE, USER_AGENT
import re
from datetime import datetime

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
}

def slugify_performer(name: str) -> str:
    """Turn 'Angela White' into 'angela-white'"""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")

def parse_date(text: str) -> Optional[str]:
    """Try to normalise various date formats to YYYY-MM-DD"""
    text = text.strip()
    # Common patterns on data18
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %Y", "%b %Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Fallback: just return cleaned text
    return text or None

async def fetch_performer_brazzers_scenes(performer: str, client: httpx.AsyncClient) -> List[SceneCandidate]:
    """
    Fetch Brazzers scenes for a performer.
    Tries the filtered studio page first, falls back to main performer page.
    """
    slug = slugify_performer(performer)
    urls_to_try = [
        f"{DATA18_BASE}/name/{slug}/studios-brazzers",
        f"{DATA18_BASE}/name/{slug}",
    ]

    scenes: List[SceneCandidate] = []

    for url in urls_to_try:
        try:
            resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=20.0)
            if resp.status_code != 200:
                continue

            tree = HTMLParser(resp.text)

            # data18 scene list items vary a bit; this targets the common pattern
            # You will almost certainly need to tweak the selectors after testing
            for item in tree.css("div.scene, div.list-item, div[id^='scene']"):
                title_el = item.css_first("a[href*='/scenes/']")
                if not title_el:
                    continue

                title = title_el.text(strip=True)
                href = title_el.attributes.get("href", "")
                scene_url = href if href.startswith("http") else DATA18_BASE + href
                scene_id = href.rstrip("/").split("/")[-1]

                # Series / site
                series = "Brazzers"
                series_el = item.css_first("a[href*='studios'], span.site, div.site")
                if series_el:
                    series = series_el.text(strip=True)

                # Date
                date = None
                date_el = item.css_first("span.date, div.date, time")
                if date_el:
                    date = parse_date(date_el.text(strip=True))

                scenes.append(
                    SceneCandidate(
                        scene_id=scene_id,
                        title=title,
                        date=date,
                        series=series,
                        url=scene_url,
                        performers=[performer],
                    )
                )

            if scenes:
                break  # success

        except Exception as e:
            print(f"[data18] Error fetching {url}: {e}")
            continue

    return scenes