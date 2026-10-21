# TempleOS-Korean 계획

> 목표: ThinkPad X61에서 실사용 가능한 한국어 TempleOS 계열 OS.
> 베이스: **ZealOS** (commit `eee210f`, 2025-11-09) → 포크명 **TempleOS-Korean**
> 언어명: **HolyC** 유지 (내부 파일 확장자 `.ZC`는 1단계에서 유지, 추후 `.HC` 개명 검토)

---

## 1. 왜 ZealOS인가

| 요구사항 | ZealOS | TinkerOS |
|---|---|---|
| SATA(AHCI) 설치 | ✅ | ✅ |
| 인터넷(TCP/IP 스택) | ✅ ARP/DHCP/DNS/ICMP/IPv4/TCP/UDP/소켓 | ❌ 스택 없음 |
| 다크 모드 | ✅ 32bit 컬러 팔레트 | △ 16색 팔레트 |
| 메뉴/문서 한글화 | ✅ DolDoc 소스 | ✅ |
| 베어메탈(X61) | ✅ AHCI, BIOS | ✅ (T61 검증 사례) |
| 확장 비용 | 낮음 (스택 보유) | 높음 (스택 포팅 필요) |

→ 네트워크 요구가 결정적. ZealOS를 포크한다.

## 2. 이름 정책

- OS 표기: `TempleOS-Korean` (boot banner, `sys_os_version_str`)
- 언어 표기: `HolyC` 유지. 소스 내 `ZealC` 문자열은 UI 번역 단계에서 `HolyC`로 치환.
- 파일 확장자 `.ZC`는 초기 유지(빌드/툴 호환). 안정화 후 `.HC` 일괄 개명 검토.
- 고유명사(TempleOS, HolyC, DolDoc, RedSea, AHCI, PCI, TCP/IP 등)는 번역하지 않는다.

## 3. 요구사항 → 구현 매핑

| # | 요구 | 구현 | 단계 |
|---|---|---|---|
| R1 | 전체 메뉴/글 한글화 | DolDoc/문자열 카탈로그 + CP949 적용 | P3~P5 |
| R2 | 고유성/사용성 유지 | 용어집, 고유명사/명령/경로 유지 | P3 |
| R3 | Unix 셸 명령 호환 | `Shell` + coreutils 부분집합 (ls, cd, cat, cp, mv, rm, mkdir, echo, grep, head, tail, wc, find, ps, kill …) | P6 |
| R4 | 다크 모드 | 팔레트/테마, 기본 다크, 토글 | P7 |
| R5 | SATA 설치 | 기존 AHCI 경로 검증 + X61 설치 문서 | P8 |
| R6 | 인터넷 연결 | ZealOS 스택 + 82566MM(ICH8 LAN) 드라이버 + DHCP/DNS | P9 |
| R7 | 확대 기능 없음 | 1× 8×8만 사용. 2×/zoom 작업 제외 | 전 단계 |
| R8 | 게임 보류 | `src/Apps`, `src/Demo` 번역 제외 | 전 단계 |

## 4. 텍스트 아키텍처 (한글의 핵심)

- 폰트: **달무리(Dalmoori) 8×8**, 현대 한글 11,172자, Apache 2.0.
- 셀: **U16**. `0x0000~0x00FF` = 기존 ASCII/CP437, `0x8100~0xFEFE` = CP949.
- 한 셀 = 한 글자 유지 → 와이드셀/연속셀 불필요.
- 파일은 CP949 바이트, 표시 버퍼만 U16.
- 폰트 데이터: `/System/FontKR.DAT` (111,736 bytes: 헤더 + 11,172 codes + 11,172 glyphs).
- 적용 범위:
  - P1(완료): `GrPrint`/`GrPutS` 경로의 CP949 렌더 (그래픽 텍스트)
  - P2: `CDocEntry.data` U16 전환 (문서/메뉴/에디터)
- 인코딩 주의: **소스에 한글을 직접 UTF-8로 쓰지 않는다.** 반드시 `tools/i18n/apply.py`로 CP949 바이트를 기록한다.

## 5. 단계와 수용 기준

### P1. 폰트/그래픽 텍스트 (완료)
- [x] 달무리 TTF → 8×8 비트맵 추출 (`tools/font/extract_dalmoori.py`)
- [x] `FontKR.DAT` 생성 (11,172자, 0 blank)
- [x] `src/System/FontKR.ZC` 로더 + 이진 탐색
- [x] `GrPutChar` → `GrPutCharBits` 분리, `GrPutS` CP949 디코드
- [x] `StartOS.ZC`에서 로드
- 수용: `FontKRRep;`가 `11172 glyphs loaded` 출력, `GrPrint`로 한글 출력

### P2. 문서 U16 전환 (최대 난관)
- `CDocEntry.data` `U8*` → `U16*`, `len` = 셀 수
- `DocPrint/DocPutS/DocGet/DocFind/DocHighlight/DocRecalc/DocEd`, 클립보드, undo
- `dollar_buf`는 ASCII 유지
- 인코딩 플래그: 레거시 문서(CP437) vs 한글 문서(CP949)
- 수용: 한글 문서 작성·저장·재로드, 커서/선택/찾기 정상

### P3. i18n 파이프라인 + UI 번역
- `tools/i18n/extract.py` → `segments.jsonl` (현재 5,962 세그먼트 / 5,039 고유)
- 서브에이전트 번역 → `lang/ko.json` (현재 400개, 검증 0 오류)
- `apply.py`로 CP949 적용 (P2 이후)
- 용어집/금지문자/포맷 보존 검증

### P4. 메뉴/대화상자 한글화
- `PersonalMenu.DD`, `System/Menu`, `DocPopUp`, 에디터 메뉴, 파일 관리자
- 수용: 모든 상위 메뉴/버튼/에러 메시지 한국어, 레이아웃 깨짐 없음

### P5. 문서/도움말 번역
- `src/Doc/*.DD` 우선순위: Welcome, Tips, HelpIndex, KeyMap, FileMgr, Boot
- ChangeLog/Charter는 제외(또는 후순위)

### P6. Unix 셸
- 명령: `ls cd pwd cat cp mv rm mkdir rmdir echo grep head tail wc touch find ps kill clear uname date help`
- 1차: 명령 dispatcher + 인자 파싱
- 2차: 파이프(`|`), 리다이렉션(`>`, `>>`), glob(`*`)
- 수용: `ls | grep .ZC`, `cat file > copy` 동작

### P7. 다크 모드
- 팔레트: 기본 다크(배경 검정/회색, 텍스트 밝은 회색, 강조 청록)
- `Ctrl-Alt-T` 토글, Registry 저장
- 수용: 재부팅 후 테마 유지

### P8. SATA 설치 검증
- QEMU(AHCI) + X61 실기
- 자동 설치 실패 시 수동 파티션/IO 포트 절차 문서화
- 수용: X61 SSD 부팅 성공

### P9. 인터넷
- ZealOS `Home/Net` 스택 활성화
- 82566MM(ICH8 LAN) 드라이버 신규 (E1000은 82545EM만 지원)
- DHCP/DNS/TCP 테스트
- 수용: `ping`/`wget`(텍스트) 동작, X61 유선 연결

### P10. 릴리스
- ISO 2종(BIOS/UEFI), 설치 문서, 라이선스(NOTICE, Apache 2.0 폰트)
- X61 8시간 안정성 테스트

## 6. 번역 운영 (서브에이전트)

- 모델: `opencode/deepseek-v4.1-flash-free` (품질/용어집 준수 우수)
- 배치: 50~100 문자열/배치, 4~8 병렬
- 입력: `lang/batches/batch_XXX.json`
- 출력: `lang/batches/out_XXX.json` (`{id: 번역}`)
- 검증: `tools/i18n/merge.py`
  - `%s/%d/%%` 보존, `$`/`$$` 개수, `\n` 개수
  - CP949 인코딩 가능, 금지 문장부호 없음, 길이 제한
- 적용: `tools/i18n/apply.py` (예정) — 바이트 범위 교체, 태그 보존

## 7. 빌드/테스트

- WSL Ubuntu 24.04, QEMU 8.2 + KVM, nbd, xorriso
- `cd build && sudo ./build-iso.sh --headless`
- 디버그: `-monitor unix:/tmp/qmon.sock` → `screendump /tmp/s.ppm`
- 산출물: `build/ZealOS-PublicDomain-BIOS-*.iso`, `build/ZealOS-BSD2-UEFI-*.iso`

## 8. 리스크

| 리스크 | 완화 |
|---|---|
| U16 문서 전환이 최대 병목 | 작은 단위 커밋, QEMU 자동 회귀 |
| 메모리 보호 없음(버그=크래시) | 단정문, 스크린샷 비교, 작은 패치 |
| CP437/CP949 충돌 | 문서별 인코딩 플래그 |
| 8×8 판독성 | 1× 고정(요구사항), UI 문구 짧게 |
| 82566 드라이버 난이도 | 1차 여행용 라우터/유선 대안, 2차 드라이버 |
| 빌드 실패 시 블라인드 | QEMU monitor screendump |

## 9. 현재 상태 (2026-10-21)

- 폰트 파이프라인/로더/그래픽 CP949 렌더 구현
- UI 문자열 400개 번역·검증 완료 (`lang/ko.json`)
- 전체 카탈로그 추출: 5,962 세그먼트
- 빌드 진행 중 (QEMU, 소스 복사 단계)
- 다음: P2 문서 U16 착수 + 나머지 UI 배치 번역

## 10. 하지 않는 것

- 2×/줌 기능
- 게임/데모 번역 (보류)
- WiFi 네이티브
- 네이티브 브라우저/TLS
- ACPI 전원관리 (초기 범위 밖)
