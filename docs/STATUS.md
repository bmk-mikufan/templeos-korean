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

## 최종 빌드 (2026-10-22 10:00)

- **`build/TempleOS-Korean-BIOS.iso` (16MB, bootable) 생성·부팅 확인**
- **검은 배경 데스크톱 확인** (표준 팔레트 0/15 인덱스 반전)
- 폰트: TempleOS 원본 8×8 ASCII/CP437 256글리프 복원
- 한글: `FontKR` 11,172자 로드 (`font_kr_num=11172`)

### 확인된 부작용

- 팔레트 0/15를 반전했기 때문에 `BLACK`(0)을 배경으로 쓰는 코드(예: `WinMax`)가 **흰색으로 칠해짐**
- 올바른 해법은 팔레트 반전이 아니라 **`KTask.ZC`의 `task->text_attr`를 `BLACK<<4+WHITE`로 바꾸고 커널 재빌드**
- 한글 픽셀 렌더 테스트(`KRTest`)는 이 부작용으로 화면이 하얗게 지워져 **육안 확인 보류**

## 다음

1. `KTask.ZC` 기본 속성 수정 + `BootHDIns` 커널 재빌드 → 팔레트는 표준으로 되돌림
2. `KRTest`를 `WinMax` 없이 그리도록 수정해 한글 픽셀 확인
3. P2: `CDocEntry.data` U16 전환 (문서/메뉴/에디터)
4. 두벌식 IME
5. 번역 적용 (`apply.py`) + 나머지 UI 문자열
6. P6: Unix 셸, P7: 다크 모드, P8: X61 SATA 검증, P9: 82566 유선 드라이버

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
