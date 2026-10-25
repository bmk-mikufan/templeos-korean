#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add Korean (CP949 + Dalmoori 8x8) rendering to an installed TempleOS 5.03.

    patch_korean.py /tmp/vdisk3 [--template DIR]

Run stage1.sh first: it copies the pristine (uncompressed) 5.03 sources from
the GitHub snapshot over the .Z files, so everything here is plain text.

All patched sources live under /Adam (JIT-compiled at boot), so the kernel
itself is untouched -- the changes take effect on the next boot.

Same design as the ZealOS port: the 32-bit text cell stays char byte + attr,
and a parallel U16 array holds the glyph index.  A Korean cell carries the
magic char 0x01; GrUpdateTextFG diverts it to GrPutKRCell().  A Hangul
syllable is two bytes of CP949, so it occupies two cells.
"""

import os
import shutil
import sys

ROOT = None
TPL = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


def P(p):
    return os.path.join(ROOT, p.lstrip('/'))


def rd(p):
    with open(P(p), 'rb') as f:
        return f.read()


def wr(p, b):
    os.makedirs(os.path.dirname(P(p)), exist_ok=True)
    with open(P(p), 'wb') as f:
        f.write(b)


def sub(p, old, new, count=1, label=''):
    d = rd(p)
    n = d.count(old)
    if n == 0 and d.count(new) > 0:
        print('  skip (already patched) %-16s %s' % (p, label))
        return
    if n != count:
        sys.exit('FAIL %s %s: expected %d match(es), found %d\n  %r'
                 % (p, label, count, n, old[:90]))
    wr(p, d.replace(old, new))
    print('  patched %-28s %s' % (p, label))


GPUT = b'''U0 GrPutKRCell(I64 ci,I64 cur_ch,I64 *dst,I64 w1,U8 *dst_start,U8 *dst_end)
{//Draw one Korean glyph cell.  ci is the cell index into gr.text_kr.
  U8 *p=dst(U8 *);
  I64 gi,i,j,save;

  if (!gr.text_kr || !font_kr_glyphs || !text.font)
    return;
  if (!(gi=gr.text_kr[ci]) || gi>font_kr_num)
    return;
  if (i=cur_ch.u16[1]&0x3FF+gr.pan_text_x+gr.pan_text_y<<5) {
    j=i&0x1F;
    if (j&0x10) j|=~0x1F;
    i>>=5;
    if (i&0x10) i|=~0x1F;
    p+=w1*i+j;
  }
  if (dst_start<=p<dst_end) {
    save=text.font[0];
    text.font[0]=font_kr_glyphs[gi-1];
    GrRopEquU8NoClipping((cur_ch&0xF00)|(cur_ch&ATTRF_UNDERLINE),p,w1);
    text.font[0]=save;
  }
}

'''

DISPATCH_OLD = b'      if (i=cur_ch.u16[1]&0x3FF+gr.pan_text_x+gr.pan_text_y<<5) {'
DISPATCH_NEW = b'''      if ((cur_ch&0xFF)==1 && gr.text_kr && gr.text_kr[src-gr.text_base-1])
\tGrPutKRCell(src-gr.text_base-1,cur_ch,dst,w1,dst_start,dst_end);
      else if (i=cur_ch.u16[1]&0x3FF+gr.pan_text_x+gr.pan_text_y<<5) {'''

START_DD = '''$WW+H,1$$FG,5$$TX+CX,"TempleOS-Korean V5.03",D="DD_OS_NAME_VERSION"$$FG$

$TX+CX,"퍼블릭 도메인 운영 체제"$

$LK,"도움말 및 색인",A="FI:::/Doc/HelpIndex.DD"$, $LK,"빠른 시작: 명령줄",A="FI:::/Doc/CmdLineOverview.DD"$
'''


def main():
    global ROOT, TPL
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ROOT = sys.argv[1]
    if len(sys.argv) >= 4 and sys.argv[2] == '--template':
        TPL = sys.argv[3]

    print('== Korean font data')
    shutil.copyfile(os.path.join(TPL, 'FontKR.DAT'), P('/Adam/FontKR.DAT'))
    print('  /Adam/FontKR.DAT %d bytes' % os.path.getsize(P('/Adam/FontKR.DAT')))

    print('== new source files')
    fk = open(os.path.join(TPL, 'FontKR.ZC'), 'rb').read()
    fk = fk.replace(b'// Data file: /System/FontKR.DAT',
                    b'// Data file: /Adam/FontKR.DAT')
    fk = fk.replace(b'::/System/FontKR.DAT', b'::/Adam/FontKR.DAT')
    fk = fk.replace(b'MemCopy(', b'MemCpy(')
    fk = fk.replace(b'MAlloc(size, sys_task)', b'MAlloc(size)')
    wr('/Adam/FontKR.HC', fk)
    print('  /Adam/FontKR.HC %d bytes' % len(fk))

    kr = open(os.path.join(TPL, 'KRText.ZC'), 'rb').read()
    wr('/Adam/KRText.HC', kr)
    print('  /Adam/KRText.HC %d bytes' % len(kr))

    print('== hangul ime')
    shutil.copyfile(os.path.join(TPL, 'HangulIME.DAT'), P('/Adam/HangulIME.DAT'))
    print('  /Adam/HangulIME.DAT %d bytes' % os.path.getsize(P('/Adam/HangulIME.DAT')))
    hime = open(os.path.join(TPL, 'HangulIME.ZC'), 'rb').read()
    wr('/Adam/HangulIME.HC', hime)
    print('  /Adam/HangulIME.HC %d bytes' % len(hime))

    print('== graphics')
    sub('/Adam/Gr/GrGlbls.HC',
        b'  U16\t*win_z_buf;',
        b'  U16\t*text_kr;\t//Korean glyph index+1 per cell, 0=none.\n'
        b'  U16\t*win_z_buf;',
        label='CGrGlbls.text_kr')

    sub('/Adam/Gr/GrInitB.HC',
        b'  gr.text_base=CAlloc(TEXT_ROWS*TEXT_COLS*sizeof(U32));',
        b'  gr.text_base=CAlloc(TEXT_ROWS*TEXT_COLS*sizeof(U32));\n'
        b'  gr.text_kr=CAlloc(TEXT_ROWS*TEXT_COLS*sizeof(U16));',
        label='alloc text_kr')

    d = rd('/Adam/Gr/GrScrn.HC')
    if b'U0 GrPutKRCell' not in d:
        d = d.replace(b'U0 GrUpdateTextFG()', GPUT + b'U0 GrUpdateTextFG()', 1)
        wr('/Adam/Gr/GrScrn.HC', d)
        print('  patched /Adam/Gr/GrScrn.HC      GrPutKRCell')
    sub('/Adam/Gr/GrScrn.HC', DISPATCH_OLD, DISPATCH_NEW, label='dispatch')

    print('== doc')
    sub('/Adam/DolDoc/DocRecalc.HC',
        b'\t\tTextLenStr(win_task,x-x0,y-y0,k,tmp_u32_attr,ptr);',
        b'\t\tTextLenStrKR(win_task,x-x0,y-y0,k,tmp_u32_attr,ptr);',
        label='TextLenStrKR')

    print('== build order')
    sub('/Adam/MakeAdam.HC',
        b'#include "Gr/MakeGr"\n',
        b'#include "FontKR"\n#include "Gr/MakeGr"\n#include "KRText"\n',
        label='MakeAdam includes')
    sub('/Adam/MakeAdam.HC',
        b'#include "Host"\nCd("..");;',
        b'#include "Host"\n#include "HangulIME"\nCd("..");;',
        label='MakeAdam hangulime')

    print('== boot')
    d = rd('/StartOS.HC')
    if b'HangulIMELoad;' in d:
        print('  skip (already patched) /StartOS.HC HangulIMELoad')
    else:
        if b'\nFontKRLoad;\n' not in d:
            d = d.replace(b'#include "/Adam/MakeAdam"\n',
                          b'#include "/Adam/MakeAdam"\n\nFontKRLoad;\n', 1)
            print('  patched /StartOS.HC              FontKRLoad')
        d = d.replace(b'\nFontKRLoad;\n', b'\nFontKRLoad;\nHangulIMELoad;\n', 1)
        if b'HangulIMELoad;' not in d:
            sys.exit('FAIL: HangulIMELoad not inserted')
        wr('/StartOS.HC', d)
        print('  patched /StartOS.HC              HangulIMELoad')

    print('== branding')
    sub('/HomeSys.HC', b'"\\nTempleOS V%5.3f', b'"\\nTempleOS-Korean V%5.3f',
        label='HomeSys banner')
    sub('/Adam/ADefine.HC', b'"TempleOS V%0.2f"', b'"TempleOS-Korean V%0.2f"',
        label='DD_OS_NAME_VERSION')

    print('== boot screen')
    wr('/Doc/Start.DD', START_DD.encode('cp949'))
    print('  wrote /Doc/Start.DD')

    print('done')


main()
