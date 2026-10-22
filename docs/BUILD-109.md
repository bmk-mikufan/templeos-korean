# 빌드 절차 (109 베이스)

## 왜 109인가

`build/AUTO.ISO`가 설치하는 커널·컴파일러는 **2.03.109**인데
저장소 `src/`는 **2.03.120**이다. 소스 전체를 그대로 복사해 빌드하면
옛 컴파일러가 새 `System/Math/Math.ZC`를 파싱하다 죽는다.

```
ERROR: Invalid lval at "*m"  C:/System/Math/Math.ZC,19
```

따라서 **설치된 109 소스를 그대로 두고**, 필요한 파일만 패치한다.
(한글 폰트, Slate 팔레트, CP949 출력, 이름/버전)

## 준비

- Linux + KVM, `qemu-system-x86_64`, `qemu-nbd`
- `build/AUTO.ISO`

호스트 코어를 그대로 주면 부팅·설치가 수 초 안에 끝난다.

```bash
qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp $(nproc) -m 2G \
  -rtc base=localtime -drive format=raw,file=disk.raw,cache=unsafe \
  -cdrom AUTO.ISO -device isa-debug-exit -display none
```

## 1. 빈 디스크에 설치

```bash
qemu-img create -f raw disk.raw 1024M
qemu-system-x86_64 ... -drive file=disk.raw -cdrom AUTO.ISO \
  -device isa-debug-exit -display none
```

AutoInstall이 끝나면 QEMU가 스스로 종료한다.

## 2. 디스크 마운트

```bash
sudo qemu-nbd -c /dev/nbd0 -f raw disk.raw
sudo partprobe /dev/nbd0
sudo mount /dev/nbd0p1 /mnt/vdisk
```

## 3. 패치

```bash
sudo python3 build/patch109.py        # FontKR, GrBitMap, MakeSystem, StartOS
sudo python3 build/unhook_startos.py  # 빌드 훅 제거 + BuildISO.ZC
sudo python3 build/final_build109.py  # KMain 브랜드, StartOS.live, BootHDIns 훅
sudo umount /mnt/vdisk
sudo qemu-nbd -d /dev/nbd0
```

`final_build109.py`가 하는 일:

- `Kernel/KMain.ZC` → `"TempleOS-Korean V%0.2f.%d"` (커널 배너)
- 현재 `StartOS.ZC`를 `/Tmp/StartOS.live`로 저장 (ISO에 들어갈 정상 버전)
- 디스크의 `StartOS.ZC` 끝에 `BootHDIns('C');` + `AutoFullDistro5` 추가
- `AutoFullDistro5.ZC`가 `/Distro/StartOS.ZC`를 `/Tmp/StartOS.live`로 덮어쓰게 수정

## 4. 빌드 실행

```bash
qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp $(nproc) -m 2G \
  -rtc base=localtime -drive file=disk.raw,cache=unsafe \
  -device isa-debug-exit -display none
```

부팅 후 자동으로:

1. `MakeSystem` (JIT, 1~2분)
2. `BootHDIns('C')` — 컴파일러 + 커널 AOT 빌드 (가장 오래 걸림)
3. `AutoFullDistro5` — `BootDVDIns`가 컴파일러/커널을 한 번 더 빌드하고 ISO 생성
4. `OutU8(0x501)` → QEMU 종료

## 5. ISO 추출

```bash
sudo qemu-nbd -c /dev/nbd0 -f raw disk.raw
sudo mount /dev/nbd0p1 /mnt/vdisk
cp /mnt/vdisk/Tmp/MyDistro.ISO.C build/TempleOS-Korean-BIOS.iso
sudo umount /mnt/vdisk
sudo qemu-nbd -d /dev/nbd0
```

## 속도에 대하여

- ZealOS 컴파일러는 **단일 스레드**다. `-smp 16`을 줘도 AOT 컴파일 시간은 거의 그대로다.
  (Linux 커널의 `make -j`처럼 병렬화되지 않는다.)
- `-cpu host`, KVM, `cache=unsafe`는 부팅·설치·파일 복사에서 체감이 크다.
- 가장 오래 걸리는 구간은 `BootHDIns` + `BootDVDIns`의 **두 번 컴파일**이다.
  한 번으로 줄이려면 `AutoFullDistro5`의 `BootDVDIns`를 건너뛰고
  이미 만든 `/Boot/Kernel.ZXE`, `/Compiler/Compiler.ZXE`를 `/Distro`에 복사하면 된다.

## 산출물

- `build/TempleOS-Korean-BIOS.iso` — 3,694,592 bytes
- md5 `2b9ed9943eb9a60c184977b73d4bb951`
- BIOS/CD 부팅 → AutoInstall → 하드디스크 부팅 확인
