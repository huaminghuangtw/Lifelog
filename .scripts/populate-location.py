"""Copy each day's journal `location` into location.json.

Only the dates already present in jdata.json are touched, so the file grows
exactly as fast as the tracked lifelog does. Run by .githooks/pre-push.
"""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JOURNAL = (
    Path(
        os.environ.get(
            "SECOND_BRAIN_VAULT",
            Path.home()
            / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Second-Brain",
        )
    )
    / "Daily-Bullet-Journal/journals"
)

LOCATION_LINE = re.compile(r"^location:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)


def journal_path(day: str) -> Path | None:
    year, month = day[:4], int(day[5:7])
    folders = sorted((JOURNAL / year).glob(f"{month:02d}-*"))
    return folders[0] / f"{day.replace('-', '_')}.md" if folders else None


def location_of(day: str) -> str | None:
    path = journal_path(day)
    if not path or not path.is_file():
        return None
    block = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not block:
        return None
    line = LOCATION_LINE.search(block.group(1))
    return line.group(1).strip("\"'") if line else None


def main() -> int:
    tracked = json.loads((REPO / "jdata.json").read_text(encoding="utf-8"))
    target = REPO / "location.json"
    current = (
        json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {}
    )

    updated = dict(current)
    missing, unchanged = [], 0
    for day in tracked:
        place = location_of(day)
        if place is None:
            if day not in updated:
                missing.append(day)
            else:
                unchanged += 1
            continue
        if updated.get(day) == place:
            unchanged += 1
            continue
        updated[day] = place

    print(f"{len(updated) - unchanged} mapped, {unchanged} unchanged")
    for place, days in Counter(updated.values()).most_common():
        print(f"  {days:3d}  {place}")
    for day in missing:
        print(f"  no journal location: {day}")

    if not missing and updated == current:
        print("location.json is up to date")
        return 0

    ordered = {day: updated[day] for day in sorted(updated)}
    target.write_text(
        json.dumps(ordered, indent=4, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
