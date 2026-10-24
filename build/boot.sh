#!/bin/bash
# unmount (if mounted) and (re)boot the test VM
pkill -9 qemu-system-x86 2>/dev/null
sleep 2
sync
umount /tmp/vdisk 2>/dev/null
qemu-nbd -d /dev/nbd0 >/dev/null 2>&1
SOCK=${1:-qmon}
SOCK=${SOCK#/tmp/}
SOCK=${SOCK%.sock}
rm -f /tmp/$SOCK.sock
setsid nohup qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 2 -m 2G \
  -rtc base=localtime -drive format=raw,file=/root/fdisk.raw,cache=unsafe \
  -display none -monitor unix:/tmp/$SOCK.sock,server,nowait \
  > /root/qboot.log 2>&1 < /dev/null &
disown
for i in $(seq 1 30); do
  [ -S /tmp/$SOCK.sock ] && { echo "sock ready, boot started $(date '+%H:%M:%S')"; exit 0; }
  sleep 0.5
done
echo "SOCKET TIMEOUT"; cat /root/qboot.log | tail -3; exit 1
