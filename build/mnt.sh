#!/bin/bash
# mount /root/fdisk.raw at /tmp/vdisk
pkill -9 qemu-system-x86 2>/dev/null
pkill -9 qemu-nbd 2>/dev/null
sleep 1
modprobe nbd max_part=8
qemu-nbd -d /dev/nbd0 >/dev/null 2>&1
sleep 1
qemu-nbd -c /dev/nbd0 -f raw /root/fdisk.raw || { echo "NBD CONNECT FAILED"; exit 1; }
sleep 1
partprobe /dev/nbd0
mkdir -p /tmp/vdisk
for i in 1 2 3 4 5; do
  if mount /dev/nbd0p1 /tmp/vdisk 2>/dev/null; then echo MOUNTED; exit 0; fi
  sleep 1
  partprobe /dev/nbd0
done
echo "MOUNT FAILED"
exit 1
