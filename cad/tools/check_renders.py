"""Render inventory check: every docs/renders/*.png is used by a doc, every render a doc uses exists.

python cad/tools/check_renders.py   (exit 1 on any failure; `make check-renders` also checks that none is out of date)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDERS = ROOT / "docs" / "renders"
DOCS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")), *sorted((ROOT / "pcb").rglob("README.md"))]
REF = re.compile(r"renders/([A-Za-z0-9_.\-]+\.png)")


def main():
    used = {}
    for doc in DOCS:
        for name in REF.findall(doc.read_text()):
            used.setdefault(name, []).append(doc.relative_to(ROOT).as_posix())
    present = {p.name for p in RENDERS.glob("*.png")}
    fails = []
    for name in sorted(present - set(used)):
        fails.append(f"docs/renders/{name} is used by no doc (remove it, or reference it)")
    for name in sorted(set(used) - present):
        fails.append(f"{name} is referenced by {', '.join(sorted(set(used[name])))} but does not exist")
    for f in fails:
        print("  FAIL", f)
    print(f"renders: {len(present)} present, {len(used)} referenced, {len(fails)} problems")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
