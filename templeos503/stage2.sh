#!/bin/bash
# Stage 2: copy the ko.json-translated tree over the image and drop .Z twins.
set -e
M=${1:-/tmp/vdisk3}
O=/root/tos503-kr
cd "$O"
n=0
find . -type f | while read -r f; do
  d=$(dirname "$M/$f")
  mkdir -p "$d"
  cp -f "$f" "$M/$f"
  rm -f "$M/$f.Z"
  n=$((n+1))
done
echo "stage2 done: $(find "$O" -type f | wc -l) files"
