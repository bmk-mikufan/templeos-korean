#!/bin/bash
# Patch the preserved build vdisk with the fixed font/system files.
set -e
DISK=/tmp/tmp.31jv33Ll7o/ZealOS.raw
MNT=/tmp/vdisk
REPO="/mnt/c/Users/bmk/Documents/기본 프로젝트/templeos-korean"
mkdir -p "$MNT"
if ! mountpoint -q "$MNT"; then
  qemu-nbd -c /dev/nbd0 -f raw "$DISK"
  partprobe /dev/nbd0 || true
  mount /dev/nbd0p1 "$MNT"
fi
cp "$REPO/src/System/FontKR.ZC" "$MNT/System/FontKR.ZC"
cp "$REPO/src/System/MakeSystem.ZC" "$MNT/System/MakeSystem.ZC"
cp "$REPO/src/System/Gr/GrBitMap.ZC" "$MNT/System/Gr/GrBitMap.ZC"
cp "$REPO/build/once_kr.txt" "$MNT/Home/Once"
[ -d "$MNT/Tmp/OSBuild/System/Gr" ] && cp "$REPO/src/System/Gr/GrBitMap.ZC" "$MNT/Tmp/OSBuild/System/Gr/GrBitMap.ZC" || true
[ -d "$MNT/Tmp/OSBuild/System" ] && cp "$REPO/src/System/FontKR.ZC" "$MNT/Tmp/OSBuild/System/FontKR.ZC" || true
[ -d "$MNT/Tmp/OSBuild/System" ] && cp "$REPO/src/System/MakeSystem.ZC" "$MNT/Tmp/OSBuild/System/MakeSystem.ZC" || true
sync
echo "--- font ---"
grep -n MAlloc "$MNT/System/FontKR.ZC"
echo "--- system ---"
head -8 "$MNT/System/MakeSystem.ZC"
umount "$MNT"
qemu-nbd -d /dev/nbd0
echo ready
