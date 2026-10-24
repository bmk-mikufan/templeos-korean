V = '/tmp/vdisk'

# blit enabled by default
p = V + '/System/Gr/GrScreen.ZC'
d = open(p, 'rb').read()
old = b'public Bool kr_blit_enable = FALSE;\n'
new = b'public Bool kr_blit_enable = TRUE;\n'
assert old in d
d = d.replace(old, new, 1)
open(p, 'wb').write(d)
print('blit default TRUE')

# plain Once
p = V + '/Once.ZC'
d = open(p, 'rb').read()
start = d.find(b'\tOnceExe;\n')
tail = d.find(b'\tswitch (sys_boot_src.u16[0])')
assert start > 0 and tail > start
head = d[:start]
new = head + b'\tOnceExe;\n\t"TempleOS-Korean V2.03.109\\n";\n' + d[tail:]
open(p, 'wb').write(new)
print('plain Once')
print(new.decode('latin1')[:600])
