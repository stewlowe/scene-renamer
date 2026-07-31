from pathlib import Path
from typing import List
import re
from .models import LocalFile

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".wmv", ".mov", ".m4v"}

def parse_performers_from_filename(filename: str) -> List[str]:
    """
    Very basic parser. Adjust to match how your files are currently named.
    Examples it tries to handle:
      - "Angela White.mp4"
      - "Angela White, Xander Corvus.mp4"
      - "Angela White & Mick Blue.mp4"
    """
    stem = Path(filename).stem
    # Remove common studio prefixes if present
    stem = re.sub(r"^(Brazzers|ZZ|Hot and Mean)[\s\-_]+", "", stem, flags=re.I)

    # Split on common separators
    parts = re.split(r"[,&+]|\band\b", stem, flags=re.I)
    performers = [p.strip() for p in parts if p.strip()]
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