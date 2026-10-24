V = '/tmp/vdisk'

# clean KRText
d = open('/mnt/c/Users/bmk/Documents/기본 프로젝트/templeos-korean/src/System/KRText.ZC', 'rb').read()
open(V + '/System/KRText.ZC', 'wb').write(d)

# strip OutU8 traces from GrScreen
p = V + '/System/Gr/GrScreen.ZC'
d = open(p, 'rb').read()
for junk in [b"\t\tOutU8(0x3F8, 'G'); OutU8(0x3F8, '1');\n",
             b"\t\tOutU8(0x3F8, '2');\n",
             b"\t\tOutU8(0x3F8, '3');\n"]:
    d = d.replace(junk, b'', 1)
assert b'OutU8' not in d, 'leftover OutU8'
open(p, 'wb').write(d)

# isolation Once
d = open('/mnt/c/Users/bmk/Documents/기본 프로젝트/templeos-korean/build/once_isolate.ZC', 'rb').read()
open(V + '/Once.ZC', 'wb').write(d)
print('applied isolate test')
