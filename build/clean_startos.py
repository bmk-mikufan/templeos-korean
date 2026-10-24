V = '/tmp/vdisk'
p = V + '/StartOS.ZC'
d = open(p, 'rb').read()
for junk in [b"OutU8(0x3F8, 'Z');\n",
             b"OutU8(0x3F8, 'L'); OutU8(0x3F8, '0' + font_kr_num % 10);\n"]:
    assert junk in d, junk
    d = d.replace(junk, b'', 1)
assert b'OutU8' not in d
open(p, 'wb').write(d)
print('startos clean')
print(d.decode('latin1'))
