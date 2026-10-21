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

## 진행 중

- QEMU 빌드 3차 진행 중 (`KEEP=1 timeout 1500`)
  - 1차: 15분 타임아웃으로 중단
  - 2차: `::/Tmp/OSBuild/System` 프롬프트에서 정지 → vdisk 삭제됨
  - 3차: 단계 3(`CopyTree OSBuild → C:/`) 파일 복사 확인, 계속 진행
- 저장소: https://github.com/bmk-mikufan/templeos-korean (기본 브랜치 `korean`)

## 다음

1. 빌드 성공 확인 → ISO 부팅 → `FontKRRep;`로 11,172자 로드 확인
2. P2: `CDocEntry.data` U16 전환 (문서/메뉴)
3. 번역 배치 024~ (나머지 UI) → 목표 3,400
4. P4: 상위 메뉴/대화상자 적용
5. P6: Unix 셸, P7: 다크 모드, P8: SATA 검증, P9: 82566 드라이버

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
