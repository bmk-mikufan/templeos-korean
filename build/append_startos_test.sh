#!/bin/bash
# Append the Korean rendering test to StartOS and bootable test setup.
set -e
MNT=/tmp/vdisk
if ! mountpoint -q "$MNT"; then
  qemu-nbd -c /dev/nbd0 -f raw /tmp/tmp.31jv33Ll7o/ZealOS.raw
  partprobe /dev/nbd0 || true
  mount /dev/nbd0p1 "$MNT"
fi
sed -i '/KRTest/d' "$MNT/StartOS.ZC"
printf '%s\n' '#include "/Home/KRTest";' >> "$MNT/StartOS.ZC"
tail -3 "$MNT/StartOS.ZC"
sync
umount "$MNT"
qemu-nbd -d /dev/nbd0
echo ready
