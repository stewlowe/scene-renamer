from pathlib import Path
from typing import List
import re
from .models import LocalFile

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".wmv", ".mov", ".m4v"}

def parse_performers_from_filename(filename: str) -> List[str]:
    stem = Path(filename).stem.lower().strip()

    # Remove common junk
    junk_patterns = [
        r"\blc\b", r"\bp\b", r"\bhd\b", r"\b4k\b", r"\b1080p\b", r"\b720p\b",
        r"\bfull\b", r"\bscene\b", r"\bxxx\b"
    ]
    for j in junk_patterns:
        stem = re.sub(j, " ", stem)

    stem = re.sub(r"[_\-\.]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()

    parts = re.split(r"[,&+]|\band\b", stem, flags=re.I)
    performers = []
    for p in parts:
        p = p.strip()
        if len(p) > 2:
            performers.append(p.title())
    return performers

def scan_folder(folder: Path, recursive: bool = True) -> List[LocalFile]:
    files: List[LocalFile] = []
    pattern = "**/*" if recursive else "*"

    for path in folder.glob(pattern):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            performers = parse_performers_from_filename(path.name)
            files.append(
                LocalFile(
                    path=path,
                    performers=performers,
                    current_name=path.name,
                )
            )
    return files
