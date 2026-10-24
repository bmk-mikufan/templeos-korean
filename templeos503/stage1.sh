#!/bin/bash
# Stage 1: put uncompressed base sources from the pristine 5.03 snapshot into the
# mounted image and drop the .Z twins, so the patcher works on plain text.
set -e
M=${1:-/tmp/vdisk3}
S=/root/tos-src

FILES="
Adam/Gr/GrGlbls.HC
Adam/Gr/GrInitB.HC
Adam/Gr/GrScrn.HC
Adam/DolDoc/DocRecalc.HC
Adam/MakeAdam.HC
Adam/ADefine.HC
StartOS.HC
HomeSys.HC
Doc/Start.DD
"

for f in $FILES; do
  if [ ! -f "$S/$f" ]; then echo "MISSING SRC $f"; exit 1; fi
  mkdir -p "$(dirname "$M/$f")"
  cp -f "$S/$f" "$M/$f"
  rm -f "$M/$f.Z"
  echo "  staged $f ($(stat -c%s "$M/$f") B)"
done
echo "stage1 done"
