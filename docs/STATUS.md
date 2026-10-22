# 상태 (2026-10-21)

## 완료

| 항목 | 내용 |
|---|---|
| 베이스 | ZealOS `eee210f` (2025-11-09) → `korean` 브랜치 |
| 이름 | boot banner `TempleOS-Korean` |
| 폰트 추출 | 달무리 TTF → 8×8, 11,172자, blank 0 |
| 폰트 데이터 | `src/System/FontKR.DAT` (111,736 bytes) |
| 로더 | `src/System/FontKR.ZC` — 이진 탐색, Adam 메모리 |
| 렌더 | `GrPutChar` → `GrPutCharBits` 분리, `GrPutS` CP949 디코드 |
| 부팅 로드 | `StartOS.ZC` → `FontKRLoad` |
| i18n 카탈로그 | 5,962 세그먼트 / 5,039 고유 |
| 번역 | **1,200 문자열** (1,033 번역, 167 기술 문자열 유지) |
| 검증 | 포맷/태그/개행/CP949/문장부호 검사 0 오류 |

## 최종 빌드 (2026-10-22 16:13)

- **`build/TempleOS-Korean-BIOS.iso` (3,694,592 bytes, BIOS/CD 부팅·설치 확인)**
  - md5 `2b9ed9943eb9a60c184977b73d4bb951`
- 커널 배너: `TempleOS-Korean V2.03.109` (`KMain.ZC` 브랜딩 후 커널 재빌드)
- 폰트: **ZealOS 원본 8×8** (`FontStd.ZC` 그대로)
- 테마: `PaletteSetSlate` — 검은/회색 배경의 다크 데스크톱
- 한글: `FontKR` 11,172자 로드, CP949 `GrPutS`
  - 터미널/Doc은 U8 셀 렌더러라 아직 깨져 보인다 → `docs/KOREAN-RENDERING.md`
- 설치: ISO를 CD로 부팅 → AutoInstall → 하드디스크 부팅 확인

### 빌드 방식 (중요)

AUTO.ISO의 커널/컴파일러는 **2.03.109**, 저장소 소스는 **2.03.120**이라
소스 전체를 그대로 재빌드하면 `System/Math/Math.ZC` 파싱 패닉이 발생한다.
이번 빌드는 **설치된 2.03.109 소스를 베이스**로 아래만 패치했다.

- `System/FontKR.ZC`, `FontKR.DAT` 추가 + `MakeSystem.ZC`에 include
- `System/Gr/GrBitMap.ZC` — CP949 `GrPutS` (109/120 파일 내용 동일)
- `System/StartOS.ZC` — `PaletteSetSlate`, `FontKRLoad`, 버전 문자열
- `Kernel/KMain.ZC` — `"TempleOS-Korean V%0.2f.%d"` + `BootHDIns('C')`로 커널 재빌드
- `Misc/Auto/AutoFullDistro5.ZC` — ISO에는 빌드 훅이 없는 `StartOS`를 넣도록 수정

`src/Kernel/KernelA.HH`의 UTF-8 `∞/π/÷`가 깨져 있던 버그도 수정했다
(`511add92`). 이 버그가 `Invalid lval at "*m"` 패닉의 실제 원인이었다.

자세한 절차는 `docs/BUILD-109.md` 참고.

## 다음

1. Doc pair-aware `TextLenStr` 구현 (터미널 한글 표시) — `docs/KOREAN-RENDERING.md`
2. P2: `CDocEntry.data` U16 전환 (문서/메뉴/에디터)
3. 두벌식 IME
4. 번역 적용 (`apply.py`) + 나머지 UI 문자열
5. P6: Unix 셸, P8: X61 SATA 검증, P9: 82566 유선 드라이버

## 알려진 이슈

- **터미널/Doc 한글 깨짐**: `GrPutS`(그래픽)에는 CP949가 있으나, Doc 렌더러는
  8비트 셀 + `TextLenStr`(바이트 단위)이라 한글이 2셀로 표시된다.
  `DocRecalc` 패치는 109 컴파일러/런타임에서 실패해 되돌렸다 → `docs/KOREAN-RENDERING.md`
- 상단 바의 `OS:`는 숫자 버전(`V2.03.109`)만 표시한다.
  `TempleOS-Korean` 이름은 커널 배너(`sys_os_version_full`)와 About에 나온다.
- Doc 본문 기본 색이 Slate 팔레트에서 붉게 보인다 (가독성은 유지).
- `GrVPutS`(세로 텍스트)는 아직 CP949 미지원 — 사용처 거의 없음
- 그래픽 문자열에서 CP437 바이트가 우연히 유효한 CP949 페어가 되면 오인 가능
  → P2에서 문서별 인코딩 플래그로 해결
- `ZealC` 문자열은 아직 남아 있음 → UI 번역 단계에서 `HolyC`로 치환
- 빌드 산출물/스크린샷은 `.gitignore` 처리

## 빌드 방법

전체 소스 재빌드(`build/build-iso.sh`)는 2.03.109 ↔ 2.03.120 불일치로 실패한다.
현재 재현 가능한 절차는 **109 베이스 + 최소 패치**이며 `docs/BUILD-109.md`에 정리했다.

```bash
# 설치 ISO를 빠르게 굽고/부팅할 때 (호스트 코어 + KVM)
qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp $(nproc) -m 2G \
  -rtc base=localtime -drive format=raw,file=disk.raw,cache=unsafe \
  -cdrom build/TempleOS-Korean-BIOS.iso -device isa-debug-exit
```

ZealOS 컴파일러는 **단일 스레드**라서 `-smp`를 늘려도 컴파일 자체는 빨라지지 않는다.
다만 부팅·설치·ISO 복사는 즉시 끝나고, `BootHDIns`(컴파일러+커널)가 가장 오래 걸린다.

## 파일 구조

```
assets/fonts/     dalmoori.ttf, FontKR.DAT, preview.png, LICENSE
docs/             TRANSLATION-GUIDE.md, GLOSSARY.md, STATUS.md
lang/             segments.jsonl, ko.json, report.txt, batches/
src/System/       FontKR.ZC, FontKR.DAT
tools/font/       extract_dalmoori.py
tools/i18n/       extract.py, batch.py, merge.py, (apply.py 예정)
PLAN.md
```
