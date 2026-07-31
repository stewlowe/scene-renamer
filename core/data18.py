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

COOKIES = {
    "data_user_captcha": "1"
}

KNOWN_SITES = [
    "Baby Got Boobs",
    "Big Wet Butts",
    "Brazzers Exxtra",
    "Hot and Mean",
    "Doctor Adventures",
    "Dirty Masseur",
    "Big Tits at School",
    "Big Tits at Work",
    "ZZ Series",
    "Pornstars Like It Big",
    "Real Wife Stories",
    "Moms in Control",
    "Teens Like It Big",
    "Milfs Like It Big",
    "Big Tits in Uniform",
    "Big Tits in Sports",
    "Asses in Public",
    "Day With A Pornstar",
    "Brazzers Vault",
]

def slugify_performer(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")

def parse_date(text: str) -> Optional[str]:
    text = text.strip()
    # Clean common extra text
    text = re.sub(r"(Release date|Released|Date)[:\s]*", "", text, flags=re.I)
    text = text.strip(" .,-")

    for fmt in (
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %Y",
        "%b %Y",
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def detect_series(text: str) -> str:
    text_lower = text.lower()
    for site in KNOWN_SITES:
        if site.lower() in text_lower:
            return site
    return "Brazzers"

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

                # Get surrounding text for series + date
                parent_text = ""
                current = a.parent
                for _ in range(4):  # go up a few levels for more context
                    if current is None:
                        break
                    parent_text += " " + current.text()
                    current = current.parent

                series = detect_series(parent_text)

                # Try to find a date in the surrounding text
                date = None
                # Look for common date patterns in the parent text
                date_match = re.search(
                    r"((?:January|February|March|April|May|June|July|August|September|October|November|December|"
                    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})"
                    r"|(\d{4}-\d{2}-\d{2})"
                    r"|(\d{1,2}/\d{1,2}/\d{4})",
                    parent_text,
                    re.I
                )
                if date_match:
                    date = parse_date(date_match.group(0))

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
