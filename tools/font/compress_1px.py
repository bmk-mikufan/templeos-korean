#!/usr/bin/env python3
"""Compress the 8x8 Hangul glyphs to 7 rows so consecutive text lines have a
1px gap (the "line spacing 1px" patch).

A Hangul cell is 8px tall and so is the glyph, so two lines of Korean touch.
The text layer's 8px pitch cannot be changed cheaply (see docs/BUILD-109.md),
so instead each glyph is shortened by one row: one row is OR-merged into a
neighbour and everything below shifts up by one row.  Row 7 is left blank,
which becomes the gap.

The merge keeps every stroke.  Glyphs whose gap row (row 4, between the
initial/vowel block and the final consonant) is already blank - about 40% of
the set - come out as a pure 1px upward shift of the final consonant.  The
rest fold the cheapest row of the lower half; rows 0-3 (initial + vowel) are
never touched, so the baseline stays put and letters such as 설/블/움 keep
their shape.

Format (unchanged, little endian):
    "KRF1" | U32 num | U32 ver | U32 pad
    U16 codes[num]   CP949 code units, ascending
    U64 glyphs[num]  8 rows, bit 0 = leftmost, byte 0 = top row

ver is bumped to 2 so the tool refuses to compress a file twice.

Usage:
    python tools/font/compress_1px.py assets/fonts/FontKR.DAT out.dat
    python tools/font/compress_1px.py --report assets/fonts/FontKR.DAT
"""
import struct
import sys
from pathlib import Path

MAGIC = b"KRF1"
VER_ORIGINAL = 1
VER_COMPRESSED = 2
ROWS = 8


def popcount(b):
    return bin(b).count("1")


GAP_ROW = 4          # blank row between the initial/vowel block and the final


def merge_cost(g, r):
    """Pixels that appear when row r is folded into its neighbour."""
    nb = g[r + 1] if r < ROWS - 1 else g[r - 1]
    return popcount(g[r] | nb) - max(popcount(g[r]), popcount(nb))


def choose_row(g):
    """Row to fold into a neighbour.

    Hangul is laid out as rows 0-3 (initial + vowel), row 4 (gap) and rows
    5-7 (final consonant).  The top block is never touched, so the glyph
    keeps its baseline; only the lower half is shortened.

    * If the gap row is blank, fold it away: the final consonant shifts up
      one pixel and nothing else changes.
    * Otherwise fold the lower row that adds the fewest pixels, ties going
      to the lowest row.  Folding downwards keeps the strokes that carry the
      letter's shape (e.g. the right leg of ㄹ) instead of thickening them.
    """
    if g[GAP_ROW] == 0:
        return GAP_ROW
    return min(range(GAP_ROW, ROWS), key=lambda r: (merge_cost(g, r), -r))


def compress_glyph(g):
    r = choose_row(g)
    out = list(g)
    if r < ROWS - 1:
        out[r] |= out[r + 1]
        del out[r + 1]
    else:
        out[r - 1] |= out[r]
        del out[r]
    out.append(0)
    return out, r


def load(path):
    d = Path(path).read_bytes()
    if d[:4] != MAGIC:
        raise SystemExit("%s: not a KRF1 file" % path)
    num, ver, pad = struct.unpack_from("<III", d, 4)
    expect = 16 + num * 2 + num * 8
    if len(d) != expect:
        raise SystemExit("%s: size %d, expected %d" % (path, len(d), expect))
    codes = list(struct.unpack_from("<%dH" % num, d, 16))
    off = 16 + num * 2
    glyphs = [list(d[off + i * 8: off + i * 8 + 8]) for i in range(num)]
    return num, ver, pad, codes, glyphs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    report_only = "--report" in sys.argv
    force = "--force" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    src = args[0]
    num, ver, pad, codes, glyphs = load(src)

    if ver >= VER_COMPRESSED and not force:
        raise SystemExit("%s: already compressed (ver=%d)" % (src, ver))

    out = []
    hist = {}
    thickened = 0
    seams = 0
    pure_shift = 0
    for g in glyphs:
        r = choose_row(g)
        hist[r] = hist.get(r, 0) + 1
        if g[r] == 0:
            pure_shift += 1
        nb = g[r + 1] if r < 7 else g[r - 1]
        if g[r] and nb:
            seams += 1
        merged, _ = compress_glyph(g)
        after = merged[r] if r < 7 else merged[r - 1]
        thickened += popcount(after) - max(popcount(g[r]), popcount(nb))
        out.append(merged)

    ink_before = sum(popcount(b) for g in glyphs for b in g)
    ink_after = sum(popcount(b) for g in out for b in g)
    assert all(len(g) == 8 and g[7] == 0 for g in out)

    print("glyphs         %d" % num)
    print("pixels         %d -> %d  (-%d overlap dedup, no stroke dropped)"
          % (ink_before, ink_after, ink_before - ink_after))
    print("pure 1px shift %d (%.1f%%)" % (pure_shift, 100.0 * pure_shift / num))
    print("merged rows with ink on both sides: %d (%.1f%%)" % (seams, 100.0 * seams / num))
    print("pixels added by thickening: %d (%.2f per glyph)" % (thickened, thickened / num))
    print("rows chosen    " + " ".join("%d:%d" % (r, hist.get(r, 0)) for r in range(8)))

    if report_only:
        return

    dst = Path(args[1])
    buf = bytearray()
    buf += MAGIC
    buf += struct.pack("<III", num, VER_COMPRESSED, 0)
    buf += struct.pack("<%dH" % num, *codes)
    for g in out:
        buf += bytes(g)
    dst.write_bytes(buf)
    print("wrote %s  %d bytes" % (dst, len(buf)))


if __name__ == "__main__":
    main()
