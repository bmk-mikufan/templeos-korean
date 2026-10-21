# 빌드 노트 (WSL + QEMU)

## 환경

- WSL2 Ubuntu 24.04
- QEMU 8.2 + KVM, `qemu-nbd`, `parted`, `xorriso`, `build-essential`
- 루트 권한: `wsl -u root -e bash -lc '...'`

## 실행

```bash
cd build
sudo ./build-iso.sh --headless
```

- `KEEP=1`을 주면 실패/중단 시 임시 vdisk를 보존한다.
- `TMPDIR` 경로가 로그 첫 줄에 출력된다.
- 두 번째 QEMU에는 `-monitor unix:/tmp/qmon.sock,server,nowait`가 붙는다.

## 자동화 흐름 (`src/Misc/Auto/AutoFullDistro0~5`)

| 단계 | 동작 |
|---|---|
| 0 | `BootMHDIns('C')`, 커널 설정, Once에 1 기록, Reboot |
| 1 | `KStart16.ZC`, `KernelA.HH` 복사, `BootHDIns`, Once에 2 |
| 2 | `Kernel/` 전체 복사, `BootHDIns`, Once에 3 |
| 3 | `CopyTree("C:/Tmp/OSBuild/", "C:/")`, `BootHDIns`, Once에 4 |
| 4 | `PopUp`로 5 실행 |
| 5 | `MakeMyISO` → `/Tmp/MyDistro.ISO.C` → `OutU8(0x501,0x31)` (QEMU 종료) |

호스트 스크립트는 QEMU 종료 후 nbd로 vdisk를 마운트해
`/Tmp/MyDistro.ISO.C`를 꺼내 Limine 하이브리드 ISO를 만든다.

## 화면 확인

```bash
python3 - <<'PY'
import socket
s=socket.socket(socket.AF_UNIX); s.connect('/tmp/qmon.sock')
s.sendall(b'screendump /tmp/s.ppm\n'); print(s.recv(80))
PY
cp /tmp/s.ppm /mnt/c/.../build/screen.ppm
```

Windows Python으로 PPM→PNG 변환 후 확인.

## 키 입력

```bash
python3 tools/dev/qemu_type.py /tmp/qmon.sock '#include "/Misc/Auto/AutoFullDistro5";'
```

## 중단 시 복구

1. `KEEP=1`로 vdisk 보존 (`/tmp/tmp.XXXX/ZealOS.raw`)
2. nbd 마운트:
   ```bash
   modprobe nbd
   qemu-nbd -c /dev/nbd0 -f raw /tmp/tmp.XXXX/ZealOS.raw
   partprobe /dev/nbd0
   mount /dev/nbd0p1 /mnt
   ```
3. `/Tmp/MyDistro.ISO.C` 존재 확인
4. 없으면 `/Home/Once`에 `#include "/Misc/Auto/AutoFullDistro5";` 기록 후 재부팅
5. QEMU 종료(`OutU8 0x501`) 후 ISO 추출

## 알려진 문제

- 15분 타임아웃으로 QEMU를 강제 종료하면 빌드가 중간에 끊긴다.
  → `timeout`을 넉넉히(25~30분) 두거나 화면을 보며 기다린다.
- 화면이 `::/Tmp/OSBuild/System` 프롬프트에서 멈춘 것처럼 보여도
  실제로는 파일 복사/컴파일이 진행 중일 수 있다(화면 갱신 지연).
- `AutoFullDistro5`는 `OutU8(0x501)`로 QEMU를 종료해야 호스트가 ISO를 꺼낸다.
