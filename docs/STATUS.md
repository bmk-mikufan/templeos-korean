# 상태 (TempleOS-Korean)

최종 갱신: 2026-10-24

## 한눈에

| 항목 | 상태 |
|---|---|
| 베이스 | ZealOS `eee210f` (2.03.109 설치본 + 최소 패치) |
| 이름 | `TempleOS-Korean` (커널 배너 포함) |
| 언어 | HolyC (변경 없음) |
| 한글 폰트 | ASCII/CP437 = **ZealOS 원본 8×8**, 한글 = **달무리 8×8** (`FontKR`) |
| 인코딩 | CP949 (2바이트) |
| 테마 | `PaletteSetSlate` — 검은/회색 |
| 한글 **렌더링** | ✅ 터미널 · Doc · 메뉴 모두 동작 |
| 한글 **메뉴/UI** | ✅ `lang/ko.json` 적용 (CP949) + `Doc/Tips.DD` 전문 번역 |
| 부팅 | ✅ BIOS (El Torito CD / USB-HDD) |
| USB | ✅ raw `.img` dd (ISO는 CD 전용) |

## 이번에 고친 것

### 1. 한글 렌더링 (터미널/Doc)

문제: Doc 셀은 8비트 문자 + 속성만 담고, 한글은 2바이트(CP949)라
`DocRecalc`이 두 셀을 각각 그려 깨졌다.

해결:

- `gr.text_kr[]` (U16, 셀당 1개) — 셀의 글리프 번호 보관
- 셀의 문자 바이트를 `0x01`로 표시 → `GrUpdateTextFG`가 `GrPutKRCell()` 호출
- `GrPutKRCell()`은 `text.font[0]`을 `font_kr_glyphs[gi-1]`로 잠깐 바꿔
  기존 8×8 블리터(`GrRopEquU8NoClipping`)로 그린다
- 색상 마스크는 **`0xF00`** (FG 니블). `0xFF00`은 배경까지 섞여 색이 깨졌다.
- `DocRecalc`의 텍스트 run은 `TextLenStrKR()` 사용 → CP949 쌍을 1글자로 계산
  (줄바꿈/커서/선택 영역이 어긋나지 않음)

### 2. 메뉴 한글화

`build/patch_korean.py`로 디스크를 패치한 뒤
`tools/i18n/apply.py`가 `lang/segments.jsonl`의 **바이트 범위**를 그대로
`lang/ko.json` 번역으로 덮어쓴다 (CP949). 태그(`$...$`), 포맷(`%d`),
이스케이프는 건드리지 않는다.

- 적용: 136개 파일, `exact 1,176` / `guarded 73` / `miss 76`
- 검증: System JIT 컴파일 성공, 데스크톱 부팅, `Ctrl-M` 개인 메뉴 한국어

> **주의**: `merge.py`는 `lang/batches/`에서 `ko.json`을 다시 만들기 때문에
> 수동 수정본을 덮어쓴다. 지금은 실행하지 말 것.

### 4. "오늘의 팁" (`Doc/Tips.DD`) 전문 번역

70개 팁 문단 전체를 한국어로 옮겼다 (`gen_tips.py`로 생성, CP949).
`$LK`/`$MA`/`$FG` 마크업과 링크 대상은 그대로 두고 표시 문자열만 번역했다.

- 제목 `Tips` → `팁` (`$TX+CX`), 부팅 시 `오늘의 팁` 창에 한국어로 출력
- **줄바꿈**: 한글은 셀 2칸을 쓰기 때문에 긴 문단이 창 밖으로 잘렸다.
  생성기가 표시 폭 38칸에서 **공백 뒤에 개행**을 넣어 미리 접는다
  (공백을 남겨야 Doc 엔진이 다시 접을 때 단어 중간에서 자르지 않는다).
- 이 파일은 **손번역본**이므로 앞으로 `apply.py` 실행 시
  `--exclude src/Doc/Tips.DD` 로 제외할 것.

### 3. 번역 문자열 검증 강화

번역이 따옴표(`"`)를 그대로 품으면 C 문자열이 조기 종료되어
`ERROR: Expecting ',' at "*a"` 같은 난해한 컴파일 오류가 난다.
→ `apply.py`가 `zc-str`/`dd-label`에서 맨 따옴표를 `\"`로 이스케이프하고,
`merge.py`가 `bare double quote` / `raw newline` / `trailing backslash`를
검사한다.

## 빌드

```bash
python3 build/patch_korean.py --root /mnt/vdisk
python3 tools/i18n/apply.py   --root /mnt/vdisk --strip-src-prefix
python3 build/final_build109.py
# QEMU 부팅 → BootHDIns + AutoFullDistro5 → 자동 종료
```

자세한 절차는 [BUILD-109.md](BUILD-109.md).

## 알려진 한계

- ISO(`RedSeaISO`)는 **El Torito 전용** — MBR 파티션 테이블이 없어
  USB에 그대로 dd 하면 부팅되지 않는다. USB는 raw `.img` 또는 Ventoy 사용.
- `Welcome`, `Terminal`, `Public Domain Operating System` 등 일부 문자열은
  아직 카탈로그에 없어 영어로 나온다.
- 8×8 한글은 획이 빽빽해 작은 글자는 다소 뭉개진다(설계상 한계).
- Doc 줄 높이가 8px(ASCII 폰트 기준)이라 한글은 행간이 0이다.
  글자가 서로 닿아 보이지만 판독은 가능하다. 행간을 늘리려면
  `FONT_HEIGHT`를 건드려야 해서 전체 레이아웃이 바뀐다 — 범위 밖.
- 링크(`$LK`)의 ASCII 글자는 한글보다 베이스라인이 1~2px 낮게 그려진다
  (ZealOS 기본 폰트와 달무리 폰트의 상단 여백 차이).
- WiFi 없음(유선만), 게임/2× 확대는 범위 밖.
