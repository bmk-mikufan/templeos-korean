#!/usr/bin/env python3
"""Extract translatable strings from TempleOS-Korean sources.

Outputs JSONL records with byte ranges so translations can be applied
without disturbing DolDoc tags or CP437 bytes.

Record:
  {"id","file","start","end","kind","source","context"}

Usage:
  python3 tools/i18n/extract.py [--include-docs] [--include-apps] > lang/segments.jsonl
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"

DD_TEXT_CMDS = {"TX", "LK", "MA", "MK"}
SKIP_PREFIX = ("::/", "/", "A:", "B:", "C:", "D:", "T:", "MN:", "FF:", "FI:", "HI:")
CMD_RE = re.compile(rb"^\$([A-Z]{2})")

# Single-word labels that are worth translating even without a space.
ONE_WORD_OK = {
    "OK", "Cancel", "Yes", "No", "Error", "Warning", "Help", "File", "Edit",
    "View", "Options", "Search", "Format", "Window", "Tools", "Compile", "Run",
    "Save", "Open", "Close", "Quit", "Exit", "Insert", "Delete", "Find",
    "Replace", "Print", "Undo", "Redo", "Cut", "Copy", "Paste", "Select",
    "All", "None", "Name", "Size", "Date", "Type", "Path", "Drive", "Disk",
    "Home", "Root", "Back", "Next", "Up", "Down", "Left", "Right", "Top",
    "Bottom", "New", "Load", "Store", "Reset", "Reboot", "Menu", "Main",
    "System", "Task", "Doc", "Color", "Font", "Sound", "Time", "User", "Mode",
    "Register", "Memory", "Screen", "Mouse", "Keyboard", "Directory",
}


def make_id(path: str, start: int) -> str:
    h = hashlib.sha1(f"{path}:{start}".encode()).hexdigest()[:12]
    return h


def looks_translatable(s: str) -> bool:
    s = s.strip()
    if len(s) < 2 or len(s) > 400:
        return False
    if not re.search(r"[A-Za-z]", s):
        return False
    if s.startswith(SKIP_PREFIX):
        return False
    if any(ord(c) < 32 and c not in "\n\t" for c in s):
        return False
    if "A=" in s or "LM=" in s or "\\x" in s:
        return False
    if re.fullmatch(r"[A-Z0-9_]+", s) and s not in ONE_WORD_OK:
        return False
    if re.search(r"\b[A-Z]{2,}_[A-Z0-9_]+\b", s):
        return False
    if " " not in s and s not in ONE_WORD_OK:
        return False
    if not re.search(r"[A-Za-z]{2,}", re.sub(r"%[-+ #0-9.]*[a-zA-Z]", "", s)):
        return False
    return True


def dd_segments(data: bytes):
    """Yield (start, end, text) for human text and label/text payloads."""
    n = len(data)
    i = 0
    text_start = 0
    out = []

    def flush(end):
        nonlocal text_start
        if end > text_start:
            raw = data[text_start:end]
            s = raw.decode("latin-1")
            if looks_translatable(s):
                out.append((text_start, end, "dd-text", s))
        text_start = end

    while i < n:
        if data[i] == 0x24:  # '$'
            flush(i)
            j = i + 1
            while j < n:
                if data[j] == 0x24:
                    if j + 1 < n and data[j + 1] == 0x24:
                        j += 2
                        continue
                    break
                j += 1
            cmd = data[i:j + 1]
            m = CMD_RE.match(cmd)
            if m:
                name = m.group(1).decode("ascii", "ignore")
                if name in DD_TEXT_CMDS:
                    # first quoted argument is the visible label/text
                    q = re.search(rb'"([^"\r\n]{2,300})"', cmd)
                    if q:
                        s = q.group(1).decode("latin-1")
                        if looks_translatable(s):
                            a = i + q.start(1)
                            b = i + q.end(1)
                            out.append((a, b, "dd-label", s))
            i = j + 1
            text_start = i
        else:
            i += 1
    flush(n)
    return out


ZC_STR_RE = re.compile(rb'"((?:[^"\\\r\n]|\\.)*)"')
FUNC_RE = re.compile(rb"(?:^|\n)\s*(?:public\s+)?(?:U0|I64|Bool|U8\s*\*|F64)\s+(\w+)\s*\(")


def zc_segments(data: bytes):
    out = []
    # build function position list for context
    funcs = [(m.start(), m.group(1).decode("latin-1")) for m in FUNC_RE.finditer(data)]
    fi = 0
    for m in ZC_STR_RE.finditer(data):
        s = m.group(1).decode("latin-1")
        if not looks_translatable(s):
            continue
        if "\\n" in s and len(s) < 4:
            continue
        # skip linker/help targets and include lines
        line_start = data.rfind(b"\n", 0, m.start()) + 1
        prefix = data[line_start:m.start()].decode("latin-1", "ignore")
        if "#include" in prefix or "A=" in prefix or "LM=" in prefix:
            continue
        while fi + 1 < len(funcs) and funcs[fi + 1][0] < m.start():
            fi += 1
        ctx = funcs[fi][1] if funcs else ""
        out.append((m.start(1), m.end(1), "zc-str", s, ctx))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-docs", action="store_true", default=True)
    ap.add_argument("--include-apps", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "lang" / "segments.jsonl"))
    args = ap.parse_args()

    files = []
    for p in SRC.rglob("*"):
        if p.suffix not in (".ZC", ".DD", ".HH"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if not args.include_apps and (rel.startswith("src/Apps/") or rel.startswith("src/Demo/")):
            continue
        if p.suffix == ".DD" and not args.include_docs:
            continue
        files.append(p)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for p in sorted(files):
            data = p.read_bytes()
            rel = p.relative_to(ROOT).as_posix()
            segs = []
            if p.suffix == ".DD":
                segs = dd_segments(data)
            else:
                for start, end, kind, s, ctx in zc_segments(data):
                    segs.append((start, end, kind, s, ctx))
            for seg in segs:
                if len(seg) == 5:
                    start, end, kind, s, ctx = seg
                else:
                    start, end, kind, s = seg
                    ctx = ""
                rec = {
                    "id": make_id(rel, start),
                    "file": rel,
                    "start": start,
                    "end": end,
                    "kind": kind,
                    "source": s,
                    "context": ctx,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                count += 1
    print(f"wrote {count} segments to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
