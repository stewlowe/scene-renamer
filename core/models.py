from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

@dataclass
class LocalFile:
    path: Path
    performers: List[str]          # parsed from filename
    current_name: str

@dataclass
class SceneCandidate:
    scene_id: str
    title: str
    date: Optional[str]            # YYYY-MM-DD if possible
    series: str                    # e.g. "Brazzers Exxtra", "Hot and Mean"
    url: str
    performers: List[str] = field(default_factory=list)
    thumbnail: Optional[str] = None

@dataclass
class MatchResult:
    local_file: LocalFile
    matched_scene: Optional[SceneCandidate] = None
    new_filename: Optional[str] = None
    status: str = "pending"        # pending / matched / skipped / error