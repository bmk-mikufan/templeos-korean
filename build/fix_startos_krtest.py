p = '/tmp/vdisk/StartOS.ZC'
b = open(p, 'rb').read()
lines = [l for l in b.split(b'\n') if b'KRTest' not in l]
lines.append(b'#include "/Home/KRTest";')
open(p, 'wb').write(b'\n'.join(lines).rstrip(b'\n') + b'\n')
print('fixed')
