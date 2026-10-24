#!/usr/bin/env python3
"""Inspect a TempleOS-Korean / ZealOS ISO.

Reports

  * El Torito boot catalog and boot image type (so we know whether the image
    can be made USB bootable),
  * whether a DOS/EFI MBR partition table is present (isohybrid),
  * and whether the Korean patch markers made it into the System sources.

    python3 build/inspect_iso.py build/TempleOS-Korean-BIOS.iso
"""
import struct
import sys
from pathlib import Path

SECT = 2048

MARKERS = [
    b"GrPutKRCell", b"TextLenStrKR", b"text_kr", b"font_kr_glyphs",
    b"FontKR", b"PaletteSetSlate", b"TempleOS-Korean",
]


def el_torito(data):
    print("-- El Torito")
    lba = None
    for s in range(16, 16 + 32):
        off = s * SECT
        vd = data[off:off + SECT]
        if len(vd) < 8:
            break
        if vd[0] == 0xFF:
            break
        if vd[1:6] != b"CD001":
            continue
        if vd[0] == 0 and b"EL TORITO SPECIFICATION" in vd:
            lba = struct.unpack_from("<I", vd, 0x47)[0]
            print(f"   boot record at sector 16+{s - 16}, catalog LBA {lba}")
    if lba is None:
        print("   no El Torito boot record")
        return
    cat = data[lba * SECT:(lba + 1) * SECT]
    if len(cat) < 64:
        print("   catalog unreadable")
        return
    print(f"   validation: {cat[0]:#04x} platform={cat[1]}")
    e = cat[32:64]
    bootable = e[0]
    media = e[1] & 0x0F
    names = {0: "no emulation", 1: "1.2MB floppy", 2: "1.44MB floppy",
             3: "2.88MB floppy", 4: "hard disk"}
    rba = struct.unpack_from("<I", e, 8)[0]
    count = struct.unpack_from("<H", e, 6)[0]
    seg = struct.unpack_from("<H", e, 2)[0]
    print(f"   bootable={bootable} media={media} ({names.get(media, '?')}) "
          f"load_seg={seg:#06x} sectors={count} image_lba={rba}")


def mbr(data):
    print("-- MBR / isohybrid")
    sig = data[510:512]
    print(f"   signature 55AA: {sig == b'\\x55\\xaa'}")
    entries = []
    for i in range(4):
        off = 446 + i * 16
        e = data[off:off + 16]
        if e == b"\x00" * 16:
            continue
        entries.append({
            "status": e[0],
            "type": e[4],
            "start": struct.unpack_from("<I", e, 8)[0],
            "count": struct.unpack_from("<I", e, 12)[0],
        })
    if entries:
        for e in entries:
            print(f"   partition type={e['type']:#04x} start={e['start']} "
                  f"sectors={e['count']}")
    else:
        print("   no partition table -> plain El Torito (CD only, no USB dd)")


def marks(data):
    print("-- Korean patch markers")
    for m in MARKERS:
        print(f"   {m.decode():20s} {data.count(m)}")


def main():
    p = Path(sys.argv[1])
    data = p.read_bytes()
    print(f"{p}  {len(data)} bytes")
    mbr(data)
    el_torito(data)
    marks(data)


if __name__ == "__main__":
    main()
