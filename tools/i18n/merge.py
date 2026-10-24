#!/usr/bin/env python3
"""Merge translated batches and validate them.

Usage:
  python3 tools/i18n/merge.py
Writes lang/ko.json (source -> translation) and lang/report.txt
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / "lang" / "batches"
OUT = ROOT / "lang" / "ko.json"
REPORT = ROOT / "lang" / "report.txt"

FMT_RE = re.compile(r"%(?:%|[-+ #0-9.*]*[diouxXeEfgGaAcspn])")
BAD_PUNCT = "…“”‘’·—–、。！？：；（）【】"


def _cp949_ok(c):
    try:
        c.encode("cp949")
        return True
    except UnicodeEncodeError:
        return False


def fmt_multiset(s):
    return sorted(FMT_RE.findall(s))


def bare_quotes(s):
    """Count double quotes that are not backslash-escaped."""
    n = i = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == '"':
            n += 1
        i += 1
    return n


def validate(src, dst):
    errs = []
    if not dst or not dst.strip():
        return ["empty"]
    if dst == src:
        # unchanged technical string (identifier/path/symbol) is allowed
        return []
    if fmt_multiset(src) != fmt_multiset(dst):
        errs.append(f"fmt {fmt_multiset(src)} != {fmt_multiset(dst)}")
    if src.count("$$") != dst.count("$$"):
        errs.append("$$ count")
    if src.count("$") != dst.count("$"):
        errs.append("$ count")
    if src.count("\\n") != dst.count("\\n"):
        errs.append("\\n count")
    if bare_quotes(dst):
        errs.append("bare double quote (must be \\\")")
    if "\n" in dst or "\r" in dst:
        errs.append("raw newline")
    if (len(dst) - len(dst.rstrip("\\"))) % 2:
        errs.append("trailing backslash")
    if any(c in dst for c in BAD_PUNCT):
        errs.append("bad punctuation")
    try:
        dst.encode("cp949")
    except UnicodeEncodeError as e:
        # allow single-byte (CP437/latin-1) characters such as ©
        bad = [c for c in dst if ord(c) >= 0x100 and not _cp949_ok(c)]
        if bad:
            errs.append(f"not cp949: {e}")
    if len(dst) > max(40, len(src) * 3):
        errs.append("too long")
    return errs


def main():
    sources = {}
    for p in sorted(BATCH.glob("batch_*.json")):
        for it in json.loads(p.read_text(encoding="utf-8")):
            sources[it["id"]] = it

    merged = {}
    problems = []
    for p in sorted(BATCH.glob("out_*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            pairs = data.items()
        else:
            pairs = []
            for it in data:
                if not isinstance(it, dict):
                    continue
                k = it.get("id")
                v = (it.get("translation") or it.get("target")
                     or it.get("ko") or it.get("korean"))
                if k and v:
                    pairs.append((k, v))
        for k, v in pairs:
            if k not in sources:
                problems.append(f"{p.name}: unknown id {k}")
                continue
            src = sources[k]["source"]
            errs = validate(src, v)
            if errs:
                problems.append(f"{k} [{p.name}] {errs}: {src!r} -> {v!r}")
            merged[src] = v
    same = sum(1 for k, v in merged.items() if k == v)
    OUT.write_text(json.dumps(merged, ensure_ascii=False, indent=1, sort_keys=True),
                   encoding="utf-8")
    lines = [f"translated: {len(merged) - same}",
             f"unchanged: {same}",
             f"entries: {len(merged)}",
             f"problems: {len(problems)}"] + problems
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:60]))


if __name__ == "__main__":
    main()
