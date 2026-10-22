import os

V = '/tmp/vdisk'
os.makedirs(f'{V}/Tmp', exist_ok=True)

# 1. Brand the kernel version string.
p = f'{V}/Kernel/KMain.ZC'
d = open(p, 'rb').read()
if b'TempleOS-Korean V%0.2f.%d' not in d:
    d = d.replace(b'"ZealOS V%0.2f.%d"', b'"TempleOS-Korean V%0.2f.%d"', 1)
    open(p, 'wb').write(d)

# 2. Keep a clean StartOS for the built ISO.
startos = open(f'{V}/StartOS.ZC', 'rb').read()
open(f'{V}/Tmp/StartOS.live', 'wb').write(startos)

# 3. Arm the on-disk build: rebuild kernel, then make the ISO.
if b"BootHDIns('C')" not in startos:
    startos = startos.rstrip() + (b"\nBootHDIns('C');\n"
                                  b'#include "/Misc/Auto/AutoFullDistro5";\n')
    open(f'{V}/StartOS.ZC', 'wb').write(startos)

# 4. Make the built ISO use the clean StartOS.
p = f'{V}/Misc/Auto/AutoFullDistro5.ZC'
d = open(p, 'rb').read()
if b'StartOS.live' not in d:
    anchor = b'\tCopyTree("/System", \t"/Distro/System");'
    assert anchor in d, 'AutoFullDistro5 anchor missing'
    d = d.replace(anchor, anchor + (b'\n\tCopy("::/Tmp/StartOS.live", "/Distro/StartOS.ZC");'
                                    b'\n\tDel("/Distro/System/BuildISO.ZC");'), 1)
    open(p, 'wb').write(d)

print('kernel brand + build armed')
