# 한글 렌더링 현황과 원인 (2026-10-22)

## 증상

- 터미널에서 `안녕하세요`가 CP437 글리프 여러 개로 깨져 보인다.
- 그러나 폰트는 정상 로드된다: `font_kr_num=11172`, `FontKR.DAT` 111,736 bytes.

## 원인

TempleOS/ZealOS의 문서(`CDoc`) 셀은 **U8 1바이트**다.

- `DocPutS`는 문자열을 바이트 단위로 `doc_e->tag`에 저장하고 `max_col`도 바이트 수로 센다.
- 화면 출력은 `DocRecalc` → `TextChar` / `TextLenStr`
  (`System/Gr/GrTextBase.ZC`의 어셈블리 extern)이 `text.font[ch]`로
  **한 셀에 1바이트 글리프**를 그린다.
- CP949 한글은 2바이트이므로 **두 셀**로 그려져 CP437 두 글자처럼 보인다.

`GrPutS`에는 CP949 분기(2바이트 → `FontKRIndex` → `GrPutCharBits`)를 넣었지만,
**Doc/터미널 경로는 `GrPutS`를 호출하지 않는다.** 그래서 그래픽 문자열
(`GrPrint`)에서만 한글이 나오고 터미널에서는 깨진다.

## 시도와 결과 (되돌림)

1. `DocRecalc`에 `DocTextLenKR` 헬퍼를 추가해 `TextLenStr` 호출을 대체
   → 109 컴파일러가 수정된 파일을 파싱하다 오류/정지.
2. `TextLenStr` 호출을 `GrPutS`(윈도우 DC 별칭)로 대체
   → 부팅 중 Doc 렌더가 멈춰 윈도우 매니저가 정지.

두 시도 모두 되돌렸고, 설치 디스크의 `System/DolDoc/DocRecalc.ZC`는
원본과 일치함을 확인했다 (40,101 bytes, md5 `032dad9ad06e8adee7fc110c9d92049d`).

## 올바른 수정 (다음 단계)

### 1안: pair-aware `TextLenStr` (권장, Doc 구조 유지)

- `TextChar`와 **같은 대상**(윈도우 텍스트/픽셀 버퍼)에 그리는 함수를 만든다.
- 런을 스캔해 ASCII는 기존 `TextChar`, 한글은 글리프 8바이트를 기록.
- 셀 폭은 2칸을 유지하고, 글리프는 왼쪽 1칸에 그리거나 2칸으로 스트레치.
- `DocRecalc`의 `DOCT_TEXT` 그리기 경로에서만 이 함수를 사용.

### 2안: U16 셀 전환 (근본)

- `CDocEntry.tag`/`len`/`max_col`, `DocPutS`, `DocGet`, `DocRecalc`,
  커서/선택, 찾기, 복사 경로를 16비트 셀로 전환.
- 한글 1글자 = 1셀, IME/편집 정합성 확보.
- 변경 범위가 커서 회귀 테스트가 필요하다.

## 다음 순서

1. pair-aware `TextLenStr` 구현 → 터미널 한글 표시.
2. 두벌식 IME (자모 조합 → CP949 완성형).
3. U16 셀 전환.
4. 16×16 한글 폰트(가독성) 검토.

## 참고

- `GrPutS`/`GrPrint`는 그래픽 컨텍스트에서 이미 한글 렌더가 가능하다.
- `GrVPutS`(세로 텍스트)는 아직 CP949 미지원.
