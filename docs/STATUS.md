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

## 최종 빌드 (2026-10-21 19:04)

- **`build/TempleOS-Korean-BIOS.iso` (44MB, bootable) 생성 및 부팅 확인**
- 부팅 스플래시: `TempleOS-Korean V2.03.120` / `Ring-0 64-Bit Operating System`
- 적용된 수정:
  - CP949 조회 캐스트 버그 수정 (`code0 = _s[0]`)
  - `FontKR` 로더 `MAlloc(sys_task)` + MakeSystem include 순서
  - **TempleOS 원본 8×8 ASCII/CP437 폰트 복원** (256글리프, 195개 차이 복구)
  - **16색 표준 팔레트 복원** (`PaletteSetSlate` → `PaletteSetStd`)
  - `limine.h` vendoring으로 빌드 네트워크 의존 제거
- 부팅/데스크톱 진입 확인, 한글 폰트 11,172자 로드 확인(`font_kr_num=11172`)

## 다음

1. 한글 글리프 **픽셀 렌더 최종 확인** (CP949 테스트 문자열, 캐스트 수정 반영)
2. P2: `CDocEntry.data` U16 전환 (문서/메뉴/에디터) ← 최대 난관
3. 두벌식 IME
4. 번역 적용 (`apply.py`) + 나머지 UI 문자열
5. P6: Unix 셸, P7: 다크 모드, P8: X61 SATA 검증, P9: 82566 유선 드라이버

## 알려진 이슈

- `GrVPutS`(세로 텍스트)는 아직 CP949 미지원 — 사용처 거의 없음
- 그래픽 문자열에서 CP437 바이트가 우연히 유효한 CP949 페어가 되면 오인 가능
  → P2에서 문서별 인코딩 플래그로 해결
- `ZealC` 문자열은 아직 남아 있음 → UI 번역 단계에서 `HolyC`로 치환
- 빌드 산출물/스크린샷은 `.gitignore` 처리

## 빌드 방법

```bash
cd build
sudo ./build-iso.sh --headless
# 산출물: ZealOS-PublicDomain-BIOS-*.iso, ZealOS-BSD2-UEFI-*.iso
```

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
