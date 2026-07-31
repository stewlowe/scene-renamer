import httpx
from selectolax.parser import HTMLParser
from typing import List, Optional
import re
from datetime import datetime
from .models import SceneCandidate
from config import DATA18_BASE, USER_AGENT

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
            resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=25.0)

            if resp.status_code != 200:
                print(f"  → Status {resp.status_code}")
                continue

            tree = HTMLParser(resp.text)

            # Look for any link that points to a scene
            for a in tree.css("a[href*='/scenes/']"):
                href = a.attributes.get("href", "")
                title = a.text(strip=True)

                if not title or len(title) < 5:
                    continue

                # Skip obvious non-scene links
                lower_title = title.lower()
                if any(x in lower_title for x in ["next", "prev", "page", "more results", "all scenes", "show more"]):
                    continue

                scene_url = href if href.startswith("http") else DATA18_BASE + href
                scene_id = href.rstrip("/").split("/")[-1]

                # Try to detect the series/site
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
                        date=None,          # we improve date later
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
