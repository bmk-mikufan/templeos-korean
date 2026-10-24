#!/usr/bin/env python3
"""Remove the on-disk ISO build hook so the installed system boots normally.

`final_build109.py` appends

    BootHDIns('C');
    #include "/Misc/Auto/AutoFullDistro5";

to StartOS.ZC and keeps a pristine copy in /Tmp/StartOS.live.  Run this after
the ISO has been produced (or before turning the disk into a USB image).

    python3 build/disarm_build.py --root /tmp/vdisk
"""
import argparse
import sys
from pathlib import Path

HOOK = b"\nBootHDIns('C');\n#include \"/Misc/Auto/AutoFullDistro5\";\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    root = Path(a.root)
    startos = root / "StartOS.ZC"
    live = root / "Tmp" / "StartOS.live"

    if live.is_file():
        data = live.read_bytes()
        print("restored StartOS.ZC from /Tmp/StartOS.live")
    else:
        data = startos.read_bytes()
        if HOOK not in data:
            print("no build hook found (already clean)")
            return
        data = data.replace(HOOK, b"\n")
        print("stripped build hook from StartOS.ZC")

    if b"BootHDIns" in data:
        sys.exit("refusing: StartOS still contains BootHDIns")

    startos.write_bytes(data)
    print(f"{startos} is clean ({len(data)} bytes)")


if __name__ == "__main__":
    main()
