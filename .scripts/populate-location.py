"""
Copy each day's journal `location` into location.json.
Only the dates already present in jdata.json are touched.
Run by .githooks/pre-push.
"""

import json
import os
import re
import sys
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


def location_of(day: str) -> str | None:
    year, month = day[:4], f"{int(day[5:7]):02d}"
    folder = next(iter(sorted((JOURNAL / year).glob(f"{month}-*"))), None)
    path = folder / f"{day.replace('-', '_')}.md" if folder else None
    if not path or not path.is_file():
        return None
    block = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    line = LOCATION_LINE.search(block.group(1)) if block else None
    return line.group(1).strip("\"'") if line else None


def main() -> int:
    tracked = json.loads((REPO / "jdata.json").read_text(encoding="utf-8"))
    target = REPO / "location.json"
    current = (
        json.loads(target.read_text(encoding="utf-8")) if target.is_file() else {}
    )

    found = {day: place for day in tracked if (place := location_of(day))}
    updated = current | found
    gaps = len(tracked) - len(found)

    if updated == current:
        print(f"unchanged: {len(updated)} days, {gaps} without a journal")
        return 0

    written = sum(1 for day, place in found.items() if current.get(day) != place)
    target.write_text(
        json.dumps(dict(sorted(updated.items())), indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"location.json: {len(updated)} days, {written} written, {gaps} without a journal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
