p = '/tmp/vdisk/StartOS.ZC'
lines = [l for l in open(p, 'rb').read().split(b'\n') if b'AutoFullDistro5' not in l]
open(p, 'wb').write(b'\n'.join(lines).rstrip(b'\n') + b'\n')
open('/tmp/vdisk/System/BuildISO.ZC', 'wb').write(b'#include "/Misc/Auto/AutoFullDistro5";\n')
print('startos unhooked; BuildISO.ZC written')
