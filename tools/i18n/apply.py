#!/usr/bin/env python3
"""Apply lang/ko.json translations onto a TempleOS-Korean source tree.

The extractor records exact byte ranges (file, start, end) into lang/segments.jsonl.
We use those ranges to rewrite *only* the bytes that belong to a human string,
so DolDoc tags, CP437 bytes, code and paths are never disturbed.

Because the build base is the installed 2.03.109 tree while the catalogue was
extracted from the 2.03.120 repository, byte offsets do not always line up.
For every file we therefore:

  1. replace at the recorded range when the bytes there still equal the source;
  2. otherwise fall back to a *guarded* replacement of the same text only when it
     occurs as a complete quoted literal / DolDoc label payload.

Translations are written back as CP949 (the on-disk text encoding).

Usage:
  python3 tools/i18n/apply.py --root /tmp/vdisk --dry-run
  python3 tools/i18n/apply.py --root /tmp/vdisk
  python3 tools/i18n/apply.py --root src --strip-src-prefix
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEG_DEFAULT = ROOT / "lang" / "segments.jsonl"
MAP_DEFAULT = ROOT / "lang" / "ko.json"

# NEVER translate these.  Kernel/KDefine.ZC holds the lexer's keyword, operator
# and directive tables; translating them turns the compiler into a random byte
# soup that spins forever when BootHDIns rebuilds Compiler.ZXE / Kernel.ZXE.
DEFAULT_EXCLUDE = ("src/Kernel/", "src/Compiler/")


def enc(text: str) -> bytes:
    """Encode a translation the same way it must live on disk (CP949)."""
    for codec in ("cp949", "latin-1", "utf-8"):
        try:
            return text.encode(codec)
        except UnicodeEncodeError:
            continue
    return text.encode("utf-8", "replace")


def escape_quotes(text: str) -> str:
    """Escape bare double quotes so the text stays inside a C / DolDoc string.

    A translation can legitimately move a DolDoc label around; if the result
    contains an unescaped '"' the compiler sees the string end early and dies
    with a confusing "Expecting ','" error.  Escaping is always correct here.
    """
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            out.append(text[i:i + 2])
            i += 2
            continue
        out.append('\\"' if c == '"' else c)
        i += 1
    return "".join(out)


def enc_kind(text: str, kind: str) -> bytes:
    if kind in ("zc-str", "dd-label"):
        text = escape_quotes(text)
    return enc(text)


def load_segments(path):
    per_file = {}
    for line in Path(path).open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        per_file.setdefault(r["file"], []).append(r)
    return per_file


def rel_to_target(rel: str, strip_src_prefix: bool) -> str:
    # rel is like "src/System/Menu.ZC" or "src/Doc/Tips.DD"
    if strip_src_prefix and rel.startswith("src/"):
        return rel[4:]
    return rel


def guarded_replace(data: bytes, src_b: bytes, dst_b: bytes, stats):
    """Replace src_b only where it is a whole quoted literal payload."""
    # $TX,"label",...  |  "..."  ->  find occurrences bounded by '"' on both sides,
    # or preceded by $XX, and a closing '"' after.
    out = bytearray()
    i = 0
    n = len(data)
    count = 0
    while True:
        j = data.find(src_b, i)
        if j < 0:
            out += data[i:]
            break
        before_ok = j > 0 and data[j - 1:j] == b'"'
        after = j + len(src_b)
        after_ok = after < n and data[after:after + 1] == b'"'
        if before_ok and after_ok:
            out += data[i:j]
            out += dst_b
            i = after
            count += 1
        else:
            out += data[i:j + 1]
            i = j + 1
    stats["guarded"] += count
    return bytes(out) if count else data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--segments", default=str(SEG_DEFAULT))
    ap.add_argument("--map", default=str(MAP_DEFAULT))
    ap.add_argument("--strip-src-prefix", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--only", default=None, help="substring filter on the file path")
    ap.add_argument("--exclude", action="append", default=None, metavar="PREFIX",
                    help="skip files whose path starts with PREFIX (repeatable)")
    ap.add_argument("--no-default-exclude", action="store_true",
                    help="do not skip src/Kernel/ and src/Compiler/")
    args = ap.parse_args()

    if args.no_default_exclude:
        excludes = tuple(args.exclude or ())
    else:
        excludes = tuple(args.exclude) if args.exclude is not None else DEFAULT_EXCLUDE

    segs = load_segments(args.segments)
    ko = json.loads(Path(args.map).read_text(encoding="utf-8"))
    ko_nonid = {k: v for k, v in ko.items() if v and v != k}
    print(f"translations (non-identity): {len(ko_nonid)}")

    root = Path(args.root)
    stats = {"files": 0, "changed_files": 0, "exact": 0, "guarded": 0,
             "miss": 0, "no_map": 0, "excluded": 0, "applied_strs": set()}

    for rel, recs in sorted(segs.items()):
        if args.only and args.only not in rel:
            continue
        if any(rel.startswith(p) for p in excludes):
            stats["excluded"] += 1
            continue
        tgt = root / rel_to_target(rel, args.strip_src_prefix)
        if not tgt.is_file():
            print(f"  (missing) {tgt}")
            continue
        stats["files"] += 1
        data = tgt.read_bytes()
        orig = data

        # pass 1: exact byte-range replacements, applied from the end backwards
        by_range = []
        for r in recs:
            s = r["source"]
            if s not in ko_nonid:
                continue
            a, b = r["start"], r["end"]
            if a < 0 or b > len(data) or a >= b:
                continue
            if data[a:b] != s.encode("latin-1"):
                stats["miss"] += 1
                continue
            by_range.append((a, b, enc_kind(ko_nonid[s], r["kind"])))
        for a, b, dst in sorted(by_range, key=lambda x: -x[0]):
            data = data[:a] + dst + data[b:]
            stats["exact"] += 1

        # pass 2: guarded literal replacement for everything still untranslated
        # (only for catalogue entries that actually occur in this file as text)
        if stats["miss"]:
            pass
        remaining = {}
        for r in recs:
            s = r["source"]
            if s in ko_nonid:
                remaining[s] = (ko_nonid[s], r["kind"])
        for s, (v, kind) in sorted(remaining.items(), key=lambda kv: -len(kv[0])):
            src_b = s.encode("latin-1")
            dst_b = enc_kind(v, kind)
            if src_b == dst_b:
                continue
            # only bother if the source still appears as a whole quoted literal
            if b'"' + src_b + b'"' not in data:
                continue
            before = stats["guarded"]
            data = guarded_replace(data, src_b, dst_b, stats)
            if stats["guarded"] != before:
                stats["applied_strs"].add(s)

        if data != orig:
            stats["changed_files"] += 1
            if args.verbose or args.dry_run:
                print(f"  changed {tgt}  ({len(orig)} -> {len(data)})")
            if not args.dry_run:
                tgt.write_bytes(data)

    print(json.dumps({k: v for k, v in stats.items() if k != "applied_strs"},
                     ensure_ascii=False, indent=1))
    print(f"distinct strings applied: {len(stats['applied_strs'])}")


if __name__ == "__main__":
    main()
