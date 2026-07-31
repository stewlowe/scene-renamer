import re
from pathlib import Path
from typing import Optional
from .models import SceneCandidate, LocalFile
from config import FILENAME_TEMPLATE, INVALID_CHARS

def clean_filename_part(text: str) -> str:
    if not text:
        return ""
    # Replace invalid Windows characters
    for ch in INVALID_CHARS:
        text = text.replace(ch, "")
    # Collapse multiple spaces / dashes
    text = re.sub(r"[\s\-]+", " ", text).strip()
    return text

def generate_filename(scene: SceneCandidate) -> str:
    series = clean_filename_part(scene.series or "Brazzers")
    date = scene.date or "0000-00-00"
    title = clean_filename_part(scene.title)

    name = FILENAME_TEMPLATE.format(
        series=series,
        date=date,
        title=title,
    )
    return name + ".mp4"   # keep original extension in real code

def apply_rename(local: LocalFile, new_name: str, dry_run: bool = True) -> Optional[Path]:
    new_path = local.path.with_name(new_name)
    if dry_run:
        print(f"[DRY-RUN] {local.path.name}  →  {new_name}")
        return new_path

    if new_path.exists():
        print(f"[SKIP] Target already exists: {new_path}")
        return None

    local.path.rename(new_path)
    print(f"[RENAMED] {local.path.name}  →  {new_name}")
    return new_path