p = '/tmp/vdisk/StartOS.ZC'
b = open(p, 'rb').read()
lines = [l for l in b.split(b'\n')
         if b'KRTest' not in l and b'AutoFullDistro5' not in l and b'BootHDIns' not in l]
lines.append(b'BootHDIns(\'C\');')
lines.append(b'#include "/Misc/Auto/AutoFullDistro5";')
open(p, 'wb').write(b'\n'.join(lines).rstrip(b'\n') + b'\n')
print('patched StartOS')
