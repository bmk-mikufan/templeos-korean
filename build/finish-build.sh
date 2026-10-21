#!/bin/bash
# Finish a preserved build vdisk: install OSBuild onto C: and make StartOS
# build the distro ISO at next boot.
set -e
DISK="$1"
if [ -z "$DISK" ] || [ ! -f "$DISK" ]; then
  echo "usage: $0 /path/to/ZealOS.raw"
  exit 1
fi
MNT=/tmp/vdisk-build
mkdir -p "$MNT"
qemu-nbd -c /dev/nbd0 -f raw "$DISK"
partprobe /dev/nbd0 || true
mount /dev/nbd0p1 "$MNT"
cp -a "$MNT/Tmp/OSBuild/." "$MNT/"
rm -f "$MNT/Home/Once"
sed -i '/AutoFullDistro5/d' "$MNT/StartOS.ZC"
printf '%s\n' '#include "/Misc/Auto/AutoFullDistro5";' >> "$MNT/StartOS.ZC"
sync
echo "--- StartOS tail ---"
tail -3 "$MNT/StartOS.ZC"
umount "$MNT"
qemu-nbd -d /dev/nbd0
echo ready
