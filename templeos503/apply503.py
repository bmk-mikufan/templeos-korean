#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply lang/ko.json onto the pristine TempleOS 5.03 snapshot (c26482b).

Unlike the ZealOS run there is no segments.jsonl for 5.03, so this works by
whole-quoted-literal replacement: the English key must appear as  "key"
(quote, text, quote) and is swapped for the CP949 bytes of the translation.
That keeps code, paths and DolDoc markup untouched.

    apply503.py --src /root/tos-src --out /root/tos503-kr
"""
import argparse
import json
import os
import shutil
import sys

SKIP_DIRS = {"Kernel", "Compiler", ".git", "AutoComplete", "Downloads"}
EXTS = (".HC", ".DD")


def enc(text):
    for codec in ("cp949", "latin-1", "utf-8"):
        try:
            return text.encode(codec)
        except UnicodeEncodeError:
            continue
    return text.encode("utf-8", "replace")


def escape_quotes(text):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/root/tos-src")
    ap.add_argument("--out", default="/root/tos503-kr")
    ap.add_argument("--map",
                    default="/mnt/c/Users/bmk/Documents/기본 프로젝트/templeos-korean/lang/ko.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ko = json.load(open(args.map, encoding="utf-8"))
    nz = {k: v for k, v in ko.items() if v and v != k}

    # skip anything that smells like a path or a bare identifier
    pairs = []
    for k, v in nz.items():
        if "/" in k or k.endswith((".HC", ".DD", ".DAT", ".TXT", ".BIN")):
            continue
        try:
            src_b = k.encode("latin-1")
        except UnicodeEncodeError:
            continue
        dst_b = enc(escape_quotes(v))
        if src_b == dst_b:
            continue
        pairs.append((src_b, dst_b))
    pairs.sort(key=lambda p: -len(p[0]))
    print("translation pairs: %d" % len(pairs))

    changed = 0
    applied = set()
    total = 0
    for dp, dn, fn in os.walk(args.src):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if not f.endswith(EXTS):
                continue
            p = os.path.join(dp, f)
            data = open(p, "rb").read()
            orig = data
            for src_b, dst_b in pairs:
                needle = b'"' + src_b + b'"'
                if needle not in data:
                    continue
                cnt = data.count(needle)
                data = data.replace(needle, b'"' + dst_b + b'"')
                applied.add(src_b)
                total += cnt
            if data != orig:
                changed += 1
                rel = os.path.relpath(p, args.src)
                print("  %-46s %+7d B" % (rel, len(data) - len(orig)))
                if not args.dry_run:
                    dst = os.path.join(args.out, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    open(dst, "wb").write(data)

    print("files changed: %d   strings applied: %d   occurrences: %d"
          % (changed, len(applied), total))


main()
