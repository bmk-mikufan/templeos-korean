#!/bin/bash
# Extract the freshly built ISO, verify it, disarm the build hook, and produce
# the USB image.  Both artifacts are copied into the Windows Downloads folder.
#
#   build/finalize.sh
#
# Run only after the QEMU distro build has exited by itself.

set -e
V=/tmp/vdisk
REPO=/root/repo
OUT=/mnt/c/Users/bmk/Downloads
ISO=TempleOS-Korean-x61.iso
IMG=TempleOS-Korean-x61-usb.img

pkill -9 qemu-system-x86 2>/dev/null || true
sleep 2
sync
echo "== mounting"
/root/mnt.sh

echo "== built ISO on disk"
ls -la "$V/Tmp/MyDistro.ISO.C"

cp "$V/Tmp/MyDistro.ISO.C" "/root/$ISO"
echo "== inspect"
python3 "$REPO/build/inspect_iso.py" "/root/$ISO" | tee /tmp/iso_report.txt

echo "== marker gate"
python3 - "/root/$ISO" <<'PY'
import sys
d = open(sys.argv[1], 'rb').read()
need = {b'GrPutKRCell': 1, b'TextLenStrKR': 1, b'text_kr': 1, b'font_kr_glyphs': 1}
bad = [k.decode() for k, n in need.items() if d.count(k) < n]
if bad:
    sys.exit("FAIL: ISO is missing Korean rendering markers: " + ", ".join(bad))
print("OK: Korean rendering markers present")
PY

echo "== disarm build hook + clean /Tmp"
python3 "$REPO/build/disarm_build.py" --root "$V"
rm -rf "$V"/Tmp/* || true
sync
umount "$V" 2>/dev/null || true
qemu-nbd -d /dev/nbd0 >/dev/null 2>&1 || true
sleep 1

echo "== USB raw image"
bash "$REPO/build/make_usb.sh" /root/fdisk.raw /root/out

echo "== copy to Downloads"
mkdir -p "$OUT"
cp -f "/root/$ISO" "$OUT/$ISO"
cp -f "/root/out/$IMG" "$OUT/$IMG"

echo "== result"
ls -lh "$OUT/$ISO" "$OUT/$IMG"
md5sum "$OUT/$ISO" "$OUT/$IMG"
