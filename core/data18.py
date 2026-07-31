import httpx
from selectolax.parser import HTMLParser
from typing import List, Optional
import re
from datetime import datetime
from .models import SceneCandidate
from config import DATA18_BASE, USER_AGENT

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Cookie that many data18 scrapers use
COOKIES = {
    "data_user_captcha": "1"
}

def slugify_performer(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")

def parse_date(text: str) -> Optional[str]:
    text = text.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %Y", "%b %Y", "%Y-%m-%d", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

async def fetch_performer_brazzers_scenes(performer: str, client: httpx.AsyncClient) -> List[SceneCandidate]:
    slug = slugify_performer(performer)

    urls_to_try = [
        f"{DATA18_BASE}/name/{slug}/studios-brazzers",
        f"{DATA18_BASE}/name/{slug}",
    ]

    scenes: List[SceneCandidate] = []

    for url in urls_to_try:
        try:
            print(f"  Trying: {url}")
            resp = await client.get(
                url,
                headers=HEADERS,
                cookies=COOKIES,
                follow_redirects=True,
                timeout=25.0
            )

            print(f"  → Status {resp.status_code}")

            if resp.status_code != 200:
                continue

            tree = HTMLParser(resp.text)

            for a in tree.css("a[href*='/scenes/']"):
                href = a.attributes.get("href", "")
                title = a.text(strip=True)

                if not title or len(title) < 5:
                    continue

                lower_title = title.lower()
                if any(x in lower_title for x in ["next", "prev", "page", "more results", "all scenes", "show more"]):
                    continue

                scene_url = href if href.startswith("http") else DATA18_BASE + href
                scene_id = href.rstrip("/").split("/")[-1]

                series = "Brazzers"
                parent_text = ""
                if a.parent:
                    parent_text = a.parent.text()

                for site in [
                    "Baby Got Boobs", "Big Wet Butts", "Brazzers Exxtra",
                    "Hot and Mean", "Doctor Adventures", "Dirty Masseur",
                    "Big Tits at School", "Big Tits at Work", "ZZ Series",
                    "Pornstars Like It Big", "Real Wife Stories", "Moms in Control"
                ]:
                    if site.lower() in parent_text.lower():
                        series = site
                        break

                scenes.append(
                    SceneCandidate(
                        scene_id=scene_id,
                        title=title,
                        date=None,
                        series=series,
                        url=scene_url,
                        performers=[performer],
                    )
                )

            # Remove duplicates
            seen = set()
            unique = []
            for s in scenes:
                if s.scene_id not in seen:
                    seen.add(s.scene_id)
                    unique.append(s)
            scenes = unique

            if scenes:
                print(f"  → Found {len(scenes)} scenes")
                break
            else:
                print(f"  → No usable scene links found")

        except Exception as e:
            print(f"  → Error: {e}")
            continue

    return scenes
