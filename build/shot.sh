#!/bin/bash
# usage: shot.sh <sockname> <outname>   e.g. shot.sh qmon93 ts1
SOCK=/tmp/${1}.sock
OUT=/tmp/${2}.ppm
python3 - "$SOCK" "$OUT" <<'PY'
import socket,time,sys
sock,out=sys.argv[1],sys.argv[2]
s=socket.socket(socket.AF_UNIX); s.settimeout(5); s.connect(sock); time.sleep(0.2)
s.recv(8192)
s.sendall(('screendump %s\n'%out).encode())
time.sleep(0.8)
s.close()
PY
ls -la "$OUT" >/dev/null && echo "shot $OUT $(date '+%H:%M:%S')"
