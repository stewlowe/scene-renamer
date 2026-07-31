import asyncio
from pathlib import Path
import httpx
from rich.console import Console
from rich.table import Table

from core.scanner import scan_folder
from core.data18 import fetch_performer_brazzers_scenes
from core.renamer import generate_filename

console = Console()

async def main():
    folder = Path(input("Enter folder path to scan: ").strip('" '))
    if not folder.exists():
        console.print("[red]Folder does not exist[/red]")
        return

    files = scan_folder(folder)
    console.print(f"Found {len(files)} video files")

    # Group by first performer for now
    performers = {}
    for f in files:
        if f.performers:
            key = f.performers[0]
            performers.setdefault(key, []).append(f)

    async with httpx.AsyncClient() as client:
        for performer, file_list in performers.items():
            console.print(f"\n[bold cyan]Performer: {performer}[/bold cyan] ({len(file_list)} files)")
            scenes = await fetch_performer_brazzers_scenes(performer, client)
            console.print(f"  Found {len(scenes)} Brazzers scenes on data18")

            if not scenes:
                continue

            # Very crude demo: just show first few candidates
            table = Table(title=f"Candidates for {performer}")
            table.add_column("Date")
            table.add_column("Series")
            table.add_column("Title")
            for s in scenes[:8]:
                table.add_row(s.date or "?", s.series, s.title[:60])
            console.print(table)

            # TODO: actual matching UI goes here later

if __name__ == "__main__":
    asyncio.run(main())