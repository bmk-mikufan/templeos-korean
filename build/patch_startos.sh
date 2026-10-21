#!/bin/bash
# Make the OS build the distro ISO automatically at boot (no keyboard needed).
set -e
DISK=/tmp/tmp.31jv33Ll7o/ZealOS.raw
MNT=/tmp/vdisk
mkdir -p "$MNT"
if ! mountpoint -q "$MNT"; then
  qemu-nbd -c /dev/nbd0 -f raw "$DISK"
  partprobe /dev/nbd0 || true
  mount /dev/nbd0p1 "$MNT"
fi
if ! grep -q 'AutoFullDistro5' "$MNT/StartOS.ZC"; then
  printf '%s\n' '#include "/Misc/Auto/AutoFullDistro5";' >> "$MNT/StartOS.ZC"
fi
rm -f "$MNT/Home/Once"
sync
echo "--- tail StartOS ---"
tail -5 "$MNT/StartOS.ZC"
umount "$MNT"
qemu-nbd -d /dev/nbd0
echo ready
