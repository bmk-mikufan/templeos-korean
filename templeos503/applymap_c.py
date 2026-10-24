#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply ko503.json to C sources, matching the literal-backslash-\\n form
that HolyC string literals actually use (the JSON holds real newlines)."""
import json
import sys


def enc(t):
    for c in ("cp949", "latin-1", "utf-8"):
        try:
            return t.encode(c)
        except UnicodeEncodeError:
            continue
    return t.encode("utf-8", "replace")


def main():
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    pairs = []
    for k, v in m.items():
        if not v or v == k:
            continue
        for kk, vv in ((k, v), (k.replace("\n", "\\n"), v.replace("\n", "\\n"))):
            pairs.append((kk.encode("latin-1"), enc(vv)))
    pairs.sort(key=lambda p: -len(p[0]))
    for path in sys.argv[2:]:
        d = open(path, "rb").read()
        o = d
        hits = 0
        for a, b in pairs:
            c = d.count(a)
            if c:
                d = d.replace(a, b)
                hits += c
        if d != o:
            open(path, "wb").write(d)
            print("  %-40s %d replacements (%+d B)" % (path, hits, len(d) - len(o)))
        else:
            print("  %-40s no change" % path)


main()
