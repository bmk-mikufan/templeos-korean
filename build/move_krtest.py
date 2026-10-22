p = '/tmp/vdisk/StartOS.ZC'
b = open(p, 'rb').read()
lines = [l for l in b.split(b'\n') if b'KRTest' not in l]
out = []
for l in lines:
    if l.strip() == b'#include "~/MakeHome"':
        out.append(b'#include "/Home/KRTest";')
    out.append(l)
open(p, 'wb').write(b'\n'.join(out))
print('inserted before MakeHome')
