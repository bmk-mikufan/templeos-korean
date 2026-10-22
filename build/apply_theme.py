import os
import subprocess

repo = '/mnt/c/Users/bmk/Documents/기본 프로젝트/templeos-korean'
os.chdir(repo)

# 1) restore upstream ZealOS font
b = subprocess.check_output(['git', 'show', 'eee210f:src/Kernel/FontStd.ZC'])
open('src/Kernel/FontStd.ZC', 'wb').write(b)

# 2) standard palette order (0=black .. 15=white)
p = 'src/System/Gr/GrPalette.ZC'
d = open(p, 'rb').read()
d = d.replace(
    b'\t0xFFFFFF, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xAA5500, 0xAAAAAA,\n'
    b'\t0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0x000000',
    b'\t0x000000, 0x0000AA, 0x00AA00, 0x00AAAA, 0xAA0000, 0xAA00AA, 0xAA5500, 0xAAAAAA,\n'
    b'\t0x555555, 0x5555FF, 0x55FF55, 0x55FFFF, 0xFF5555, 0xFF55FF, 0xFFFF55, 0xFFFFFF')
open(p, 'wb').write(d)

# 3) dark Slate palette
p = 'src/System/Gr/GrInitB.ZC'
d = open(p, 'rb').read().replace(b'PaletteSetStd;', b'PaletteSetSlate;')
open(p, 'wb').write(d)

# 4) brand the running system as TempleOS-Korean
p = 'src/StartOS.ZC'
d = open(p, 'rb').read()
marker = b'#include "/System/MakeSystem"\n'
add = (b'sys_os_version_str = "TempleOS-Korean V2.03.120";\n'
       b'sys_os_version_nice = sys_os_version_str;\n'
       b'sys_os_version_full = sys_os_version_str;\n')
if add not in d:
    d = d.replace(marker, marker + add)
open(p, 'wb').write(d)
print('applied')
