#!/usr/bin/env python3
"""Apply the TempleOS-Korean patches to an installed 2.03.109 build base.

The repo sources are 2.03.120 but build/AUTO.ISO installs a 2.03.109 system,
and a full 120 rebuild panics in System/Math/Math.ZC.  The reproducible build
therefore patches the *installed* tree (see docs/BUILD-109.md).

This script is idempotent: run it as often as you like against either a fresh
109 install or an already-patched tree.

    python3 build/patch_korean.py --root /tmp/vdisk --check
    python3 build/patch_korean.py --root /tmp/vdisk

It performs:

  System/Gr/GrGlobals.ZC   add  U16 *text_kr;      (Korean cell layer)
  System/Gr/GrInitB.ZC     alloc gr.text_kr
  System/Gr/GrScreen.ZC    add  GrPutKRCell + hook in GrUpdateTextFG
  System/KRText.ZC         CP949 pair decoder -> TextCharKR / TextLenStrKR
  System/DolDoc/DocRecalc.ZC  Doc text run uses TextLenStrKR
  System/FontKR.ZC         font loader / binary search (with precedence fix)
  System/FontKR.DAT        11,172 glyphs
  System/HangulIME.ZC      two-beolsik IME (KeyDev hook, in-place composition)
  System/HangulIME.DAT     CP949 syllable table
  System/MakeSystem.ZC     #include FontKR + KRText + HangulIME
  StartOS.ZC               PaletteSetSlate + FontKRLoad + HangulIMELoad + version branding
  Once.ZC                  Korean boot greeting
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ASSETS = ROOT / "assets"

GRSCREEN_FN = r'''U0 GrPutKRCell(I64 ci, I64 cur_ch, I64 *dst, I64 w1, U8 *dst_start, U8 *dst_end)
{//Draw one Korean glyph cell.  Byte 1 of the cell selects this routine and
//gr.text_kr[] holds the glyph number (1-based) for that cell.
	U8 *p = dst(U8 *);
	I64 gi, i, j, save;

	if (!gr.text_kr || !font_kr_glyphs || !text.font)
		return;
	if (!(gi = gr.text_kr[ci]) || gi > font_kr_num)
		return;
	if (i = cur_ch.u16[1] & 0x3FF + gr.pan_text_x + gr.pan_text_y << 5)
	{
		j = i & 0x1F;
		if (j & 0x10)
			j |= ~0x1F;
		i >>= 5;
		if (i & 0x10)
			i |= ~0x1F;
		p += w1 * i + j;
	}
	if (dst_start <= p < dst_end)
	{
		save = text.font[0];
		text.font[0] = font_kr_glyphs[gi - 1];
		GrRopEquU8NoClipping((cur_ch & 0xF00) | (cur_ch & ATTRF_UNDERLINE), p, w1);
		text.font[0] = save;
	}
}

'''

GRSCREEN_OLD_CHAIN = """\t\t\tif (i = cur_ch.u16[1]&0x3FF+gr.pan_text_x+gr.pan_text_y<<5) {"""
GRSCREEN_NEW_CHAIN = """\t\t\tif ((cur_ch & 0xFF) == 1 && gr.text_kr && gr.text_kr[src - gr.text_base - 1])
\t\t\t\tGrPutKRCell(src - gr.text_base - 1, cur_ch, dst, w1, dst_start, dst_end);
\t\t\telse if (i = cur_ch.u16[1]&0x3FF+gr.pan_text_x+gr.pan_text_y<<5) {"""

# remove the old debug scaffolding if a development build left it behind
DEBUG_GLOBALS = "public I64 kr_except_ch = 0;\npublic Bool kr_blit_enable = TRUE;\n\n"
DEBUG_GUARD = "if (!kr_blit_enable || !gr.text_kr"
CLEAN_GUARD = "if (!gr.text_kr"
DEBUG_TRY = """\t\t\t{
\t\t\t\ttry
\t\t\t\t\tGrPutKRCell(src - gr.text_base - 1, cur_ch, dst, w1, dst_start, dst_end);
\t\t\t\tcatch
\t\t\t\t\tkr_except_ch = Fs->except_ch;
\t\t\t}"""
CLEAN_CALL = "\t\t\t\tGrPutKRCell(src - gr.text_base - 1, cur_ch, dst, w1, dst_start, dst_end);"


class Report:
    def __init__(self, check):
        self.check = check
        self.done, self.skip, self.fail = [], [], []

    def ok(self, what):
        (self.skip if self.check else self.done).append(what)

    def did(self, what):
        self.done.append(what)

    def bad(self, what):
        self.fail.append(what)


def read(p):
    return p.read_bytes()


def write(p, b, report, what):
    if report.check:
        report.did(what + " (would patch)")
    else:
        p.write_bytes(b)
        report.did(what)


def patch_text(p, f, report, what):
    b = read(p)
    nb = f(b)
    if nb is None:
        report.ok(what + " (already)")
    elif nb == b:
        report.ok(what + " (no change)")
    else:
        write(p, nb, report, what)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    if not (root / "System" / "MakeSystem.ZC").is_file():
        sys.exit(f"{root} does not look like a TempleOS-Korean disk")

    r = Report(args.check)

    # ---- 1. gr.text_kr declaration ------------------------------------
    def g_globals(b):
        if b"text_kr" in b:
            return None
        old = b"\tU16\t\t\t*win_z_buf;"
        if old not in b:
            return b
        return b.replace(old, old + b"\n\tU16\t\t\t*text_kr;\t//Korean glyph index + 1 per cell, 0=none.", 1)
    patch_text(root / "System/Gr/GrGlobals.ZC", g_globals, r, "GrGlobals.ZC  U16 *text_kr")

    # ---- 2. allocate the layer ----------------------------------------
    def g_initb(b):
        if b"gr.text_kr" in b:
            return None
        old = b"\tgr.text_base\t\t\t= CAlloc(TEXT_ROWS * TEXT_COLS * sizeof(U32));"
        if old not in b:
            return b
        return b.replace(old, old + b"\n\tgr.text_kr\t\t\t= CAlloc(TEXT_ROWS * TEXT_COLS * sizeof(U16));", 1)
    patch_text(root / "System/Gr/GrInitB.ZC", g_initb, r, "GrInitB.ZC   alloc gr.text_kr")

    # ---- 3. GrPutKRCell + hook ----------------------------------------
    def g_screen(b):
        s = b.decode("latin-1")
        orig = s
        if "public I64 kr_except_ch" in s:
            s = s.replace(DEBUG_GLOBALS, "", 1)
            s = s.replace(DEBUG_TRY, CLEAN_CALL, 1)
            s = s.replace(DEBUG_GUARD, CLEAN_GUARD)
        if "GrPutKRCell" not in s:
            anchor = "U0 GrUpdateTextFG()"
            if anchor not in s:
                return b
            s = s.replace(anchor, GRSCREEN_FN + anchor, 1)
        if GRSCREEN_OLD_CHAIN in s and "GrPutKRCell(src - gr.text_base" not in s:
            s = s.replace(GRSCREEN_OLD_CHAIN, GRSCREEN_NEW_CHAIN, 1)
        return None if s == orig else s.encode("latin-1")
    patch_text(root / "System/Gr/GrScreen.ZC", g_screen, r, "GrScreen.ZC  GrPutKRCell + hook")

    # ---- 4. KRText / FontKR / FontKR.DAT ------------------------------
    for rel, srcp in [("System/KRText.ZC", SRC / "System/KRText.ZC"),
                      ("System/FontKR.ZC", SRC / "System/FontKR.ZC"),
                      ("System/FontKR.DAT", SRC / "System/FontKR.DAT"),
                      ("System/HangulIME.ZC", SRC / "System/HangulIME.ZC"),
                      ("System/HangulIME.DAT", SRC / "System/HangulIME.DAT"),
                      ("StartOS.ZC", SRC / "StartOS.ZC")]:
        tgt = root / rel
        if not srcp.is_file():
            r.bad(f"{rel}  (missing source {srcp})")
            continue
        if tgt.is_file() and read(tgt) == read(srcp):
            r.ok(f"{rel}  up to date")
        else:
            if not args.check:
                shutil.copyfile(srcp, tgt)
            r.did(f"{rel}  copied from repo")

    # ---- 5. DocRecalc: pair-aware text run ----------------------------
    def doc_recalc(b):
        old = b"TextLenStr(win_task, x - x0, y - y0, k, tmp_u32_attr, ptr);"
        if b"TextLenStrKR(win_task" in b:
            return None
        if old not in b:
            return b
        return b.replace(old, old.replace(b"TextLenStr(", b"TextLenStrKR("), 1)
    patch_text(root / "System/DolDoc/DocRecalc.ZC", doc_recalc, r, "DocRecalc.ZC  TextLenStrKR")

    # ---- 6. MakeSystem includes ---------------------------------------
    def make_system(b):
        s = b.decode("latin-1")
        out = s
        if '#include "FontKR"' not in out:
            out = out.replace('#include "Externs"', '#include "Externs"\n#include "FontKR"', 1)
        if '#include "KRText"' not in out:
            out = out.replace('#include "Sound"', '#include "KRText"\n#include "Sound"', 1)
        if '#include "HangulIME"' not in out:
            out = out.replace('#include "KRText"', '#include "KRText"\n#include "HangulIME"', 1)
        return None if out == s else out.encode("latin-1")
    patch_text(root / "System/MakeSystem.ZC", make_system, r, "MakeSystem.ZC  includes")

    # ---- 7. Korean greeting -------------------------------------------
    once = ASSETS / "Once.ZC"
    if once.is_file():
        tgt = root / "Once.ZC"
        if tgt.is_file() and read(tgt) == read(once):
            r.ok("Once.ZC      up to date")
        else:
            if not args.check:
                shutil.copyfile(once, tgt)
            r.did("Once.ZC      copied from assets")

    print("TempleOS-Korean patch report" + ("  (check only)" if args.check else ""))
    for x in r.done:
        print(f"  [patch] {x}")
    for x in r.skip:
        print(f"  [ ok  ] {x}")
    for x in r.fail:
        print(f"  [FAIL ] {x}")
    if r.fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
