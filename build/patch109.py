import shutil

REPO = '/mnt/c/Users/bmk/Documents/기본 프로젝트/templeos-korean/src'
V = '/tmp/vdisk'

shutil.copyfile(f'{REPO}/System/FontKR.ZC', f'{V}/System/FontKR.ZC')
shutil.copyfile(f'{REPO}/System/FontKR.DAT', f'{V}/System/FontKR.DAT')
shutil.copyfile(f'{REPO}/System/Gr/GrBitMap.ZC', f'{V}/System/Gr/GrBitMap.ZC')

p = f'{V}/System/MakeSystem.ZC'
d = open(p, 'rb').read()
if b'#include "FontKR"' not in d:
    d = d.replace(b'#include "Memory"\n', b'#include "Memory"\n#include "FontKR"\n', 1)
open(p, 'wb').write(d)

p = f'{V}/StartOS.ZC'
d = open(p, 'rb').read()
anchor = b'#include "/System/MakeSystem"'
add = (b'#include "/System/MakeSystem"\n'
       b'PaletteSetSlate;\n'
       b'FontKRLoad;\n'
       b'if (!font_kr_num)\n'
       b'\tPrintErr("FontKR: Korean font not loaded\\n");\n'
       b'sys_os_version_str = "TempleOS-Korean V2.03.109";\n'
       b'sys_os_version_nice = sys_os_version_str;\n'
       b'sys_os_version_full = sys_os_version_str;')
if b'PaletteSetSlate;' not in d:
    d = d.replace(anchor, add, 1)
if b'AutoFullDistro5' not in d:
    d = d.rstrip() + b'\n#include "/Misc/Auto/AutoFullDistro5";\n'
open(p, 'wb').write(d)

print('patched 109 vdisk')
