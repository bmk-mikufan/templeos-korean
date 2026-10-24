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

## 3. 패치 + 번역

> **반드시 지킬 것**: 번역은 `System/`, `Home/`, `Doc/`, `PersonalMenu.DD`,
> `StartOS.ZC` 에만 적용한다. `Kernel/`과 `Compiler/`는 **절대 번역 금지**.
> 특히 `Kernel/KDefine.ZC`(238개 문자열)는 렉서의 키워드·연산자·지시자
> 테이블이라, 번역되면 `BootHDIns`가 `Compiler.ZXE`를 다시 빌드할 때
> 컴파일러가 깨져 **CPU 100%로 무한 루프**에 빠진다(디스크 I/O 0).
> `apply.py`는 기본값으로 이 두 디렉터리를 건너뛴다(`--no-default-exclude`로 해제).

```bash
# 3-1. 한글 패치 (멱등: /tmp/vdisk 어디에나 반복 실행 가능)
sudo python3 build/patch_korean.py --root /mnt/vdisk --check
sudo python3 build/patch_korean.py --root /mnt/vdisk

# 3-2. UI 번역 적용 (lang/ko.json → CP949, 바이트 범위 교체)
sudo python3 tools/i18n/apply.py --root /mnt/vdisk --strip-src-prefix --dry-run
sudo python3 tools/i18n/apply.py --root /mnt/vdisk --strip-src-prefix

# 3-3. 전체 문서 복사 (없으면 부팅 시 ::/Doc/Start.DD 오류)
sudo cp -f src/Doc/*.DD src/Doc/*.ZC /mnt/vdisk/Doc/

# 3-4. ISO 빌드 훅 장전
sudo python3 build/final_build109.py
sudo umount /mnt/vdisk
sudo qemu-nbd -d /dev/nbd0
```

`patch_korean.py`가 하는 일:

| 파일 | 변경 |
|---|---|
| `System/Gr/GrGlobals.ZC` | `U16 *text_kr;` 추가 (한글 셀 레이어) |
| `System/Gr/GrInitB.ZC` | `gr.text_kr` 할당 |
| `System/Gr/GrScreen.ZC` | `GrPutKRCell()` + `GrUpdateTextFG` 훅 |
| `System/KRText.ZC` | CP949 2바이트 디코더 `TextCharKR`/`TextLenStrKR` |
| `System/DolDoc/DocRecalc.ZC` | Doc 텍스트 run을 `TextLenStrKR`로 |
| `System/FontKR.ZC` / `.DAT` | 폰트 로더 + 11,172 글리프 |
| `System/MakeSystem.ZC` | `FontKR`, `KRText` include |
| `StartOS.ZC` | `PaletteSetSlate`, `FontKRLoad`, 버전 |
| `Once.ZC` | 한국어 부팅 인사 |

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

| 파일 | 부팅 | 용도 |
|---|---|---|
| `build/TempleOS-Korean-BIOS.iso` | BIOS / CD (El Torito) | CD 굽기, VM |
| `build/TempleOS-Korean-x61-usb.img` | BIOS / USB-HDD | USB에 dd (가장 확실) |

## 6. USB 이미지 만들기

```bash
# 6-1. 빌드 훅 해제 + /Tmp 정리 후 마운트 해제
sudo python3 build/disarm_build.py --root /mnt/vdisk
sudo rm -rf /mnt/vdisk/Tmp/*
sudo umount /mnt/vdisk && sudo qemu-nbd -d /dev/nbd0

# 6-2. 사용된 섹터까지만 잘라 raw 이미지 생성
build/make_usb.sh /root/fdisk.raw /root/out

# 6-3. USB에 기록 (Linux)
sudo dd if=/root/out/TempleOS-Korean-x61-usb.img of=/dev/sdX bs=4M conv=fsync status=progress
```

Windows에서는 Rufus(**DD 모드**) 또는 balenaEtcher로 `.img`를 굽는다.

> **중요**: 네이티브 ZealOS ISO(`RedSeaISO`)는 El Torito 전용이라
> MBR 파티션 테이블이 없다. ISO 파일을 USB에 그대로 dd 하면 부팅되지 않는다.
> USB 부팅은 **raw `.img`** 또는 **Ventoy**를 사용한다.

## 7. 검증

```bash
python3 build/inspect_iso.py build/TempleOS-Korean-BIOS.iso
build/usb_test.sh build/TempleOS-Korean-x61-usb.img
```

`inspect_iso.py`가 `GrPutKRCell`, `TextLenStrKR`, `text_kr`, `font_kr_glyphs`를
모두 1 이상 보고하면 한글 렌더링 수정이 ISO에 들어간 것이다.

## 8. 현재 쓰는 빠른 경로 (2026-10-24)

`BootHDIns` + `AutoFullDistro5`를 한 번에 돌리면 컴파일이 두 번 일어나고
급할 때 커널 없는 ISO가 나오기 쉽다. 지금은 **단계별 부팅**으로 나눈다.

```bash
# 8-1. 커널이 이미 /Boot/Kernel.ZXE, /Boot/DVDKernel.ZXE 에 있다고 가정.
#      StartOS.ZC 는 pristine(1457 B) 상태여야 한다. /Tmp/StartOS.live 에 백업.

# 8-2. ISO만 다시 만들기 (컴파일 없음, 13초)
bash arm_lean.sh          # StartOS.ZC 에 KRLeanISO() 주입
bash watch_build.sh qbuild 150   # 부팅 → /Tmp/MyDistro.ISO.C 생성 → exit=99

# 8-3. 추출 + 훅 해제 + USB 이미지 + Downloads 복사
cd /root/repo && bash build/finalize.sh
```

`arm_lean.sh`의 `KRLeanISO()`는 `/Distro`를 새로 만들고 `CopyTree`로
`/Home /System /Apps /Compiler /Demo /Doc /Kernel /Misc /Downloads`를 복사한 뒤
`/Boot/DVDKernel.ZXE`를 `/Distro/Boot/Kernel.ZXE`로 넣고 `RedSeaISO`를 부른다.
`RedSeaISO`의 출력 이름은 반드시 `FileNameAbs()`를 거쳐야 한다.

### 삽질 기록: AHCI 행(hang)

**잘라낸 USB 이미지(39 MB)에서 빌드하면 안 된다.** 파티션은 1 GB로 선언되어
있어 새 파일이 41 MB 지점에 기록되는데, 그 너머는 파일 끝(EOF)이라
`AHCIPortCmdWait` 타임아웃 → ZealOS Debugger. 항상 **1 GB 원본 `fdisk.raw`**에서
빌드하고, 자르는 것은 마지막 `make_usb.sh` 단계에서만 한다.

### `Doc/Tips.DD` 취급

`src/Doc/Tips.DD`는 손번역본이다. `apply.py`를 다시 돌릴 때는

```bash
python3 tools/i18n/apply.py --root /mnt/vdisk --strip-src-prefix \
    --exclude src/Doc/Tips.DD
```

로 제외한다. 팁 본문을 고칠 때는 `gen_tips.py`(임시 스크립트)로 다시 생성하고
`/Doc/Tips.DD`에 복사한 뒤 8-2부터 다시 돌린다.
