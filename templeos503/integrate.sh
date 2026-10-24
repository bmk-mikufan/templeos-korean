#!/bin/bash
# Integrate the finished doc translations into the master image:
# stage2 (ko.json tree) -> patcher -> ko503.json on the boot scripts.
pkill -9 qemu-system-x86 2>/dev/null
sleep 2
umount /tmp/vdisk3 2>/dev/null
qemu-nbd -d /dev/nbd2 >/dev/null 2>&1
sleep 1

echo "== staging tree check"
ls -l /root/tos503-kr/Doc/Tips.DD /root/tos503-kr/Doc/Customize.DD \
      /root/tos503-kr/Doc/StandBy.DD /root/tos503-kr/Doc/HelpIndex.DD \
      /root/tos503-kr/Once.HC 2>&1

bash /mnt/c/Users/bmk/AppData/Local/Temp/opencode/mnt_tos.sh /root/tos.raw || exit 1
bash /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/stage2.sh /tmp/vdisk3 || exit 1
python3 /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/patch_korean.py /tmp/vdisk3 \
  --template /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/templates || exit 1

echo "== ko503 boot strings"
python3 /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/applymap.py \
  /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/ko503.json \
  /tmp/vdisk3/Once.HC /tmp/vdisk3/HomeSys.HC /tmp/vdisk3/Doc/StandBy.DD

echo "== verify image"
python3 - <<'PY'
for p in ['Doc/Tips.DD', 'Doc/Customize.DD', 'Doc/StandBy.DD', 'Doc/HelpIndex.DD']:
    d = open('/tmp/vdisk3/' + p, 'rb').read()
    try:
        d.decode('cp949')
        ok = 'ok'
    except Exception as e:
        ok = 'FAIL %s' % e
    kr = sum(1 for b in d if b >= 0x81)
    print('  %-22s %6d B  cp949 %-4s  korean bytes %d' % (p, len(d), ok, kr))
for p in ['Once.HC', 'HomeSys.HC']:
    d = open('/tmp/vdisk3/' + p, 'rb').read()
    print('  %-22s %6d B  korean bytes %d' % (p, len(d), sum(1 for b in d if b >= 0x81)))
PY
sync
umount /tmp/vdisk3
qemu-nbd -d /dev/nbd2 >/dev/null 2>&1
echo "== ok"
