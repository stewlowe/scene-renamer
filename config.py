from pathlib import Path

# Base folders
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "matches.db"

# data18
DATA18_BASE = "https://www.data18.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# Filename template: series-date-title
# Example result: Brazzers Exxtra-2024-06-24-B.r.i. [brazzers Research Institute]
FILENAME_TEMPLATE = "{series}-{date}-{title}"

# Characters to strip/replace in titles for Windows safety
INVALID_CHARS = r'<>:"/\|?*'