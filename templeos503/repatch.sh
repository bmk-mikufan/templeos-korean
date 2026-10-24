#!/bin/bash
# kill VM, mount tos.raw rw, run stage1 + stage2 + patcher
pkill -9 qemu-system-x86 2>/dev/null
sleep 2
bash /mnt/c/Users/bmk/AppData/Local/Temp/opencode/mnt_tos.sh /root/tos.raw || exit 1
bash /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/stage1.sh /tmp/vdisk3 || exit 1
bash /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/stage2.sh /tmp/vdisk3 || exit 1
python3 /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/patch_korean.py /tmp/vdisk3 \
  --template /mnt/c/Users/bmk/AppData/Local/Temp/opencode/tos503/templates || exit 1
sync
echo "== ok"
