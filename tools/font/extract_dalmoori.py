#!/usr/bin/env python3
"""Extract Dalmoori 8x8 Hangul glyphs into TempleOS-Korean font data.

Output format (little endian):
    magic   U8[4]  = "KRF1"
    num     U32    number of glyphs
    ver     U32    format version (1)
    pad     U32
    codes   U16[num]  CP949 code units, ascending
    glyphs  U64[num]  8 rows x 8 columns, bit 0 = leftmost pixel,
                      byte 0 = top row (matches sys_font_std layout)

Usage:
    python tools/font/extract_dalmoori.py assets/fonts/dalmoori.ttf assets/fonts/FontKR.DAT
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HANGUL_FIRST = 0xAC00
HANGUL_LAST = 0xD7A3
FONT_PX = 8
SUPERSAMPLE = 8  # render at 64px, then average 8x8 blocks


def render_glyph(font, ch: str):
    """Rasterize one character to an 8x8 list of rows (bit 0 = leftmost)."""
    size = FONT_PX * SUPERSAMPLE
    img = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(img)
    # Dalmoori: upem=64, glyph box y=-8..56, so baseline row is 56 at 64px
    draw.text((0, 56), ch, font=font, fill=255, anchor="ls")
    rows = []
    block = SUPERSAMPLE
    for y in range(FONT_PX):
        bits = 0
        for x in range(FONT_PX):
            # average coverage of the 8x8 block
            total = 0
            for yy in range(block):
                for xx in range(block):
                    total += img.getpixel((x * block + xx, y * block + yy))
            if total >= (block * block * 255) / 2:
                bits |= 1 << x
        rows.append(bits)
    return rows


def pack(rows):
    v = 0
    for y, bits in enumerate(rows):
        v |= (bits & 0xFF) << (y * 8)
    return v


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    ttf = Path(sys.argv[1])
    out = Path(sys.argv[2])
    font = ImageFont.truetype(str(ttf), FONT_PX * SUPERSAMPLE)

    codes = []
    glyphs = []
    missing = []
    blank = []
    for cp in range(HANGUL_FIRST, HANGUL_LAST + 1):
        ch = chr(cp)
        try:
            raw = ch.encode("cp949")
        except UnicodeEncodeError:
            missing.append(ch)
            continue
        if len(raw) != 2:
            missing.append(ch)
            continue
        rows = render_glyph(font, ch)
        if not any(rows):
            blank.append(ch)
        codes.append((raw[0] << 8) | raw[1])
        glyphs.append(pack(rows))

    order = sorted(range(len(codes)), key=lambda i: codes[i])
    codes = [codes[i] for i in order]
    glyphs = [glyphs[i] for i in order]

    with out.open("wb") as f:
        f.write(b"KRF1")
        f.write(struct.pack("<III", len(codes), 1, 0))
        for c in codes:
            f.write(struct.pack("<H", c))
        for g in glyphs:
            f.write(struct.pack("<Q", g))

    print(f"glyphs: {len(codes)}")
    print(f"missing cp949: {len(missing)} {''.join(missing[:20])}")
    print(f"blank glyphs: {len(blank)} {''.join(blank[:20])}")
    print(f"output: {out} ({out.stat().st_size} bytes)")

    # preview: sample sentence + pangram, drawn from the extracted bits
    sample = [
        "다람쥐 헌 쳇바퀴에 타고파",
        "닭갈비, 읽었다, 뷁, 똠방각하",
        "안녕하세요. TempleOS-Korean 한글화 테스트입니다.",
        "시스템 전체 한글화가 가능할까? 검증해 보자.",
    ]
    code_to_bits = dict(zip(codes, glyphs))
    scale = 4
    width = max(len(s) for s in sample) * FONT_PX
    img = Image.new("1", (width + 8, len(sample) * 12 + 8), 0)
    px = img.load()
    for li, s in enumerate(sample):
        x0 = 4
        y0 = 4 + li * 12
        for ch in s:
            cp = ord(ch)
            if 0xAC00 <= cp <= 0xD7A3:
                raw = ch.encode("cp949")
                bits = code_to_bits.get((raw[0] << 8) | raw[1], 0)
                for yy in range(8):
                    row = (bits >> (yy * 8)) & 0xFF
                    for xx in range(8):
                        if row >> xx & 1:
                            px[x0 + xx, y0 + yy] = 1
            elif ch != " ":
                # ASCII is drawn as a filled box placeholder in this preview
                for yy in range(8):
                    for xx in range(8):
                        if yy in (0, 7) or xx in (0, 7):
                            px[x0 + xx, y0 + yy] = 1
            x0 += 8
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(
        out.with_name("preview.png")
    )
    print(f"preview: {out.with_name('preview.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
