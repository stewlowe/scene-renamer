import asyncio
from pathlib import Path
import httpx
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from core.scanner import scan_folder
from core.data18 import fetch_performer_brazzers_scenes
from core.renamer import generate_filename, apply_rename
from core.models import MatchResult

console = Console()

async def main():
    folder = Path(input("Enter folder path to scan: ").strip('" '))
    if not folder.exists():
        console.print("[red]Folder does not exist[/red]")
        return

    files = scan_folder(folder)
    console.print(f"\nFound {len(files)} video files\n")

    # Group by first performer
    performers = {}
    for f in files:
        if f.performers:
            key = f.performers[0]
            performers.setdefault(key, []).append(f)

    matches: list[MatchResult] = []

    async with httpx.AsyncClient() as client:
        for performer, file_list in performers.items():
            console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            console.print(f"[bold cyan]Performer: {performer}[/bold cyan] ({len(file_list)} files)")
            console.print(f"[bold cyan]{'='*60}[/bold cyan]")

            scenes = await fetch_performer_brazzers_scenes(performer, client)
            console.print(f"Found {len(scenes)} Brazzers scenes on data18\n")

            if not scenes:
                for f in file_list:
                    matches.append(MatchResult(local_file=f, status="no_scenes"))
                continue

            # Show candidates once for this performer
            table = Table(title=f"Candidates for {performer}")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Date", width=12)
            table.add_column("Series", width=22)
            table.add_column("Title")

            for idx, s in enumerate(scenes, 1):
                table.add_row(
                    str(idx),
                    s.date or "?",
                    s.series,
                    s.title[:55]
                )
            console.print(table)
            console.print()

            # Now go through each file for this performer
            for f in file_list:
                console.print(f"[bold yellow]File:[/bold yellow] {f.current_name}")
                console.print(f"Performers detected: {', '.join(f.performers)}")

                while True:
                    choice = Prompt.ask(
                        "Enter number of matching scene (or 's' to skip, 'q' to quit)",
                        default="s"
                    ).strip().lower()

                    if choice == "q":
                        console.print("[red]Quitting...[/red]")
                        return
                    if choice == "s":
                        matches.append(MatchResult(local_file=f, status="skipped"))
                        console.print("[dim]Skipped[/dim]\n")
                        break

                    try:
                        num = int(choice)
                        if 1 <= num <= len(scenes):
                            selected = scenes[num - 1]
                            new_name = generate_filename(selected)

                            console.print(f"\n[green]Selected:[/green] {selected.title}")
                            console.print(f"[green]New name:[/green] {new_name}")

                            confirm = Confirm.ask("Confirm this match?", default=True)
                            if confirm:
                                matches.append(
                                    MatchResult(
                                        local_file=f,
                                        matched_scene=selected,
                                        new_filename=new_name,
                                        status="matched"
                                    )
                                )
                                console.print("[bold green]Matched![/bold green]\n")
                                break
                            else:
                                console.print("[dim]Okay, choose again[/dim]")
                        else:
                            console.print("[red]Number out of range[/red]")
                    except ValueError:
                        console.print("[red]Please enter a number, 's', or 'q'[/red]")

    # Summary
    console.print(f"\n[bold]{'='*60}[/bold]")
    console.print("[bold]MATCHING SUMMARY[/bold]")
    console.print(f"[bold]{'='*60}[/bold]")

    matched = [m for m in matches if m.status == "matched"]
    skipped = [m for m in matches if m.status == "skipped"]
    no_scenes = [m for m in matches if m.status == "no_scenes"]

    console.print(f"Matched : {len(matched)}")
    console.print(f"Skipped : {len(skipped)}")
    console.print(f"No scenes found: {len(no_scenes)}")

    if matched:
        console.print("\n[bold]Pending renames:[/bold]")
        for m in matched:
            console.print(f"  {m.local_file.current_name}")
            console.print(f"  → {m.new_filename}\n")

        do_rename = Confirm.ask("\nApply these renames now?", default=False)
        if do_rename:
            for m in matched:
                apply_rename(m.local_file, m.new_filename, dry_run=False)
            console.print("\n[bold green]Renames applied![/bold green]")
        else:
            console.print("\n[dim]No files were renamed (dry run).[/dim]")

if __name__ == "__main__":
    asyncio.run(main())
