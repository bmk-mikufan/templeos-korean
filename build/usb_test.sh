#!/bin/bash
# Boot-test a raw disk image the way a USB stick would be booted.
#
#   build/usb_test.sh <image> [sock] [seconds]
#
# Attaches the image as a USB mass-storage device on an otherwise diskless
# machine, so a successful boot proves the image works from USB.

set -e
IMG="${1:?usage: usb_test.sh <image> [sock] [seconds]}"
SOCK="${2:-/tmp/qusb.sock}"
WAIT="${3:-60}"

pkill -9 qemu-system-x86 2>/dev/null || true
sleep 2
rm -f "$SOCK"

echo "usb boot test: $IMG  $(date '+%H:%M:%S')"
qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 2 -m 1G \
  -rtc base=localtime \
  -drive if=none,id=usbdisk,format=raw,file="$IMG" \
  -device qemu-xhci -device usb-storage,drive=usbdisk \
  -display none -monitor "unix:$SOCK,server,nowait" \
  > /root/qusb.log 2>&1 &

sleep "$WAIT"
/root/shot.sh "$SOCK" usb 2>&1 || true
python3 /mnt/c/Users/bmk/AppData/Local/Temp/opencode/ppm2png.py /tmp/usb.ppm \
  /mnt/c/Users/bmk/AppData/Local/Temp/opencode/png/usb.png 1 2>&1 || true
