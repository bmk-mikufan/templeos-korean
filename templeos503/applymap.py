#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plain substring replacement of a JSON string map inside given files.

    applymap.py MAP.json FILE [FILE ...]

Keys/values are UTF-8 in the JSON; output is CP949.  Unlike the guarded
replacer this does not require the text to be a whole quoted literal, because
some of the strings live inside escaped quotes ("...\\"Tip of the Day\\"...").
"""
import json
import sys


def enc(text):
    for codec in ("cp949", "latin-1", "utf-8"):
        try:
            return text.encode(codec)
        except UnicodeEncodeError:
            continue
    return text.encode("utf-8", "replace")


def main():
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    pairs = [(k.encode("latin-1"), enc(v)) for k, v in m.items() if v and v != k]
    pairs.sort(key=lambda p: -len(p[0]))
    for path in sys.argv[2:]:
        data = open(path, "rb").read()
        orig = data
        hits = 0
        for a, b in pairs:
            c = data.count(a)
            if c:
                data = data.replace(a, b)
                hits += c
        if data != orig:
            open(path, "wb").write(data)
            print("  %-40s %d replacements (%+d B)"
                  % (path, hits, len(data) - len(orig)))
        else:
            print("  %-40s no change" % path)


main()
