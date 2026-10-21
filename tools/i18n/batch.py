#!/usr/bin/env python3
"""Build translation batches from lang/segments.jsonl.

Prioritises menus/labels and UI messages before long documentation text.

Usage:
  python3 tools/i18n/batch.py --limit 800 --batch-size 100
  python3 tools/i18n/batch.py --kind dd-text --limit 400 --batch-size 50
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEG = ROOT / "lang" / "segments.jsonl"
OUT = ROOT / "lang" / "batches"

UI_CTX = re.compile(
    r"PopUp|Menu|DocPrint|Print|FileMgr|Ed|Win|Task|Shell|Install|Boot|Format|"
    r"Dsk|Drive|Dir|File|Compile|Option|Settings|Config|Rep|Prompt|Error",
    re.I,
)
BAD_START = set(")]},.;:?!*/\\")
BAD_END = (" at ", " and ", " or ", ", ", " (", " [", " = ", ": ")


def score(r):
    s = r["source"]
    f = r["file"]
    v = 0
    if r["kind"] == "dd-label":
        v += 4
    if r["kind"] == "dd-text":
        v -= 3
    if f.startswith(("src/System/", "src/Kernel/", "src/StartOS.ZC", "src/PersonalMenu.DD")):
        v += 5
    if "ChangeLog" in f or "Charter" in f:
        v -= 20
    if UI_CTX.search(r.get("context", "")):
        v += 3
    if " " in s:
        v += 1
    if len(s) >= 12:
        v += 1
    if s[:1] in BAD_START:
        v -= 4
    if s.endswith(BAD_END):
        v -= 3
    if s.count("%") and not re.search(r"[A-Za-z]{3,}", re.sub(r"%[-+ #0-9.]*[a-zA-Z]", "", s)):
        v -= 3
    if "\n" in s:
        v -= 1
    # skip code-ish tokens such as identifiers with underscores/casts
    if re.fullmatch(r"[\w:.]+(?: [\w:.]+)+", s) and ("_" in s or "." in s or "(" in s):
        v -= 8
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=600)
    ap.add_argument("--batch-size", type=int, default=100)
    ap.add_argument("--kind", default="ui")
    ap.add_argument("--outdir", default=str(OUT))
    args = ap.parse_args()

    seen = {}
    for line in SEG.open(encoding="utf-8"):
        r = json.loads(line)
        if args.kind == "ui" and r["kind"] == "dd-text":
            continue
        if args.kind == "docs" and r["kind"] != "dd-text":
            continue
        s = r["source"]
        if s not in seen or score(r) > seen[s]["score"]:
            seen[s] = {"source": s, "score": score(r), "context": r.get("context", ""),
                       "file": r["file"], "kind": r["kind"]}

    items = sorted(seen.values(), key=lambda x: (-x["score"], -len(x["source"])))
    items = items[: args.limit]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()

    n = 0
    for i in range(0, len(items), args.batch_size):
        chunk = items[i:i + args.batch_size]
        batch = []
        for j, it in enumerate(chunk):
            batch.append({
                "id": f"u{i + j:04d}",
                "source": it["source"],
                "where": f'{it["file"]} ({it["kind"]})',
                "hint": it["context"],
            })
        p = outdir / f"batch_{i // args.batch_size:03d}.json"
        p.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
        n += 1
    print(f"wrote {n} batches, {len(items)} strings, top score {items[0]['score'] if items else '-'}")
    for it in items[:5]:
        print(f'  {it["score"]:3d}  {it["source"][:70]!r}')


if __name__ == "__main__":
    main()
