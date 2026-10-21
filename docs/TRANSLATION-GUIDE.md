# 번역 가이드 (TempleOS-Korean)

## 1. 절대 규칙

1. **소스 파일을 UTF-8로 직접 편집하지 않는다.**
   HolyC 소스/문서는 CP949 바이트로 저장한다. 편집은 반드시
   `tools/i18n/apply.py`를 통해 바이트 범위를 교체한다.
   (일반 에디터로 한글을 입력하면 UTF-8이 되어 OS에서 깨진다.)
2. 고유명사·명령·경로·식별자는 번역하지 않는다.
3. 포맷 지정자(`%s`, `%d`, `%02d`, `%%`)와 DolDoc 태그(`$FG,...$`, `$$...$$`)를
   글자 하나도 바꾸지 않는다.
4. ASCII 문장부호만 사용한다: `. , : ? ! ( )`.
   `… “ ” ‘ ’ · — – 、 。 ！ ？ ： ； （ ）` 금지.
5. 원문의 `\n`, `\t`, `\\` 개수를 유지한다.

## 2. 번역하지 않는 것

| 분류 | 예 |
|---|---|
| 제품/언어 | TempleOS, HolyC, DolDoc, RedSea, ZealOS, AHCI, PCI, TCP/IP, DHCP, DNS |
| 함수/API/식별자 | `DocPrint`, `MAlloc`, `BootHDIns`, `sys_font_std` |
| 경로 | `::/Doc`, `/System/FontKR.DAT`, `C:/Home` |
| 명령/키 | `Dir;`, `Cd`, `<CTRL-t>`, `Ctrl-Alt-Del`, `F7`, `ESC` |
| 버전/에러 코드 | `V2.03.120`, `0x1F`, `E1000` |
| 게임/앱 고유명 | AfterEgypt, Talons, X-Caliber, TempleNES (보류) |

## 3. 문체

| 유형 | 규칙 | 예 |
|---|---|---|
| 메뉴/버튼 | 짧은 명사형 | `저장`, `취소`, `파일 관리자` |
| 대화상자 문장 | `~습니다` | `파일을 찾을 수 없습니다.` |
| 질문 | `~하시겠습니까?` | `변경 사항을 저장하시겠습니까?` |
| 지시 | `~하십시오.` | `디스크를 삽입하십시오.` |
| 상태/라벨 | 명사 + 콜론 | `상태:`, `크기:`, `경로:` |

- 한글 1음절 = 1셀. 메뉴 라벨은 가능한 12셀 이내.
- 영문과 한글 사이는 공백 1칸.
- 숫자/단위는 원문 유지: `%d bytes` → `%d 바이트`.

## 4. 검증

`python3 tools/i18n/merge.py`가 자동 검사한다.

- 모든 id 존재, 빈 번역 없음
- 포맷 지정자 다중집합 일치
- `$` / `$$` 개수 일치
- `\n` 개수 일치
- CP949 인코딩 가능
- 금지 문장부호 없음
- 길이 ≤ max(40, 원문×3)

## 5. 배치 작업 흐름

```
tools/i18n/extract.py   → lang/segments.jsonl
tools/i18n/batch.py     → lang/batches/batch_NNN.json
(서브에이전트 번역)      → lang/batches/out_NNN.json
tools/i18n/merge.py     → lang/ko.json + lang/report.txt
tools/i18n/apply.py     → src/* (CP949)     [P2 이후]
```

## 6. 서브에이전트 프롬프트 요약

- 모델: `opencode/deepseek-v4.1-flash-free`
- 역할: TempleOS-Korean UI 번역
- 입력/출력 경로 명시
- 용어집 포함
- "다른 파일 수정 금지"
- 완료 시 `done <count>`만 응답
