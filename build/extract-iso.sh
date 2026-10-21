#!/bin/bash
# Extract /Tmp/MyDistro.ISO.C from a vdisk.
set -e
DISK="$1"
OUT="$2"
if [ -z "$DISK" ] || [ -z "$OUT" ]; then
  echo "usage: $0 /path/to/ZealOS.raw /path/to/out.iso"
  exit 1
fi
MNT=/tmp/vdisk-out
mkdir -p "$MNT"
qemu-nbd -c /dev/nbd0 -f raw "$DISK"
partprobe /dev/nbd0 || true
mount /dev/nbd0p1 "$MNT"
ls -l "$MNT/Tmp/MyDistro.ISO.C"
cp "$MNT/Tmp/MyDistro.ISO.C" "$OUT"
sync
umount "$MNT"
qemu-nbd -d /dev/nbd0
ls -l "$OUT"
echo extracted
