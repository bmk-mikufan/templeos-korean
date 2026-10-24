import os
V = '/tmp/vdisk'

# fast path in KRText
exec(open('/mnt/c/Users/bmk/Documents/기본 프로젝트/templeos-korean/build/fix_fastpath.py').read())

# DocRecalc: call TextLenStrKR
p = V + '/System/DolDoc/DocRecalc.ZC'
d = open(p, 'rb').read()
old = b'TextLenStr(win_task, x - x0, y - y0, k, tmp_u32_attr, ptr);'
assert old in d
d = d.replace(old, b'TextLenStrKR(win_task, x - x0, y - y0, k, tmp_u32_attr, ptr);', 1)
open(p, 'wb').write(d)
print('DocRecalc patched')
