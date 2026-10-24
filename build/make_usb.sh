#!/bin/bash
# Build the USB-deliverable artifacts from the installed test disk.
#
#   build/make_usb.sh [DISK] [OUTDIR]
#
# Produces OUTDIR/TempleOS-Korean-x61-usb.img, a raw image of the installed
# system.  Write it to a USB stick with:
#
#   Linux : sudo dd if=TempleOS-Korean-x61-usb.img of=/dev/sdX bs=4M status=progress conv=fsync
#   Windows: use balenaEtcher / Rufus (DD mode) on the .img
#
# The image is a compacted copy of the disk (only used blocks), so the result
# is much smaller than the 1 GiB sparse disk.

set -e
DISK="${1:-/root/fdisk.raw}"
OUTDIR="${2:-/root/out}"
mkdir -p "$OUTDIR"

IMG="$OUTDIR/TempleOS-Korean-x61-usb.img"
echo "== disk: $DISK"
echo "== out : $IMG"

# 1. shrink to the last used sector so the image stays small
python3 - "$DISK" "$IMG" <<'PY'
import os, sys
src, dst = sys.argv[1], sys.argv[2]
size = os.path.getsize(src)
used = size
# walk backwards over 4 KiB chunks that are entirely zero
CH = 4096
with open(src, 'rb') as f:
    pos = size
    while pos > 0:
        start = max(0, pos - CH)
        f.seek(start)
        if f.read(pos - start).strip(b'\x00'):
            break
        pos = start
    used = pos
    # round up to 1 MiB
    used = (used + (1 << 20) - 1) & ~((1 << 20) - 1)
    f.seek(0)
    left = used
    with open(dst, 'wb') as o:
        while left:
            b = f.read(min(1 << 20, left))
            if not b:
                break
            o.write(b)
            left -= len(b)
print(f"used {used} bytes of {size}")
PY
ls -lh "$IMG"
echo "done"
