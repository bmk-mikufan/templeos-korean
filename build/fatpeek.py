import struct

f = open('/root/fdisk.raw', 'rb')
mbr = f.read(512)
parts = []
for i in range(4):
    e = mbr[446 + i*16:446 + (i+1)*16]
    boot, typ = e[0], e[4]
    lba, cnt = struct.unpack('<II', e[8:16])
    if cnt:
        parts.append((i, hex(typ), lba, cnt))
print('parts', parts)
base = parts[0][2] * 512
print('part1 byte offset', base)

f.seek(base)
bs = f.read(512)
print('OEM', bs[3:11])
bps, spc, resv, nfats, rootent, tot16, media, fatsz16 = struct.unpack('<HBHBHHBH', bs[11:11+13])
tot32 = struct.unpack('<I', bs[32:36])[0]
fatsz32 = struct.unpack('<I', bs[36:40])[0]
print('bps', bps, 'spc', spc, 'resv', resv, 'nfats', nfats, 'fatsz16', fatsz16,
      'fatsz32', fatsz32, 'tot32', tot32, 'media', hex(media))
fat_off = base + resv * bps
for i in range(nfats):
    f.seek(fat_off + i * fatsz32 * bps)
    print('FAT%d' % (i+1), f.read(32).hex())
