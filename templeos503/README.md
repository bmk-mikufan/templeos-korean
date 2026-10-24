# TempleOS-Korean V5.03

테리 데이비스의 마지막 배포판 **TempleOS 5.03** 을 그대로 두고, 한글만 읽고 쓸 수 있게
덧붙인 판입니다. 화면은 원본 그대로 640×480 / 16색이고, 커널은 한 줄도 고치지 않았습니다.

| | |
|---|---|
| 베이스 | `TempleOS.ISO` (templeos.org, 17,350,656 B, md5 `2facf5d7cfa08de4c47aede4a64cfb44`) |
| 소스 기준 | `cia-foundation/TempleOS` @ `c26482b` |
| 이름 | `TempleOS-Korean` / 언어 이름 `HolyC` 유지 |
| 문자 | ASCII·CP437 = 원본 8×8 폰트, 한글 = 달무리 8×8 (`FontKR`), 인코딩 CP949 |

## 어떻게 들어갔나

원본 5.03은 모든 소스가 `.HC.Z` 로 압축되어 있습니다. 그래서 커널을 다시 빌드하지
않고, 부팅할 때 JIT로 컴파일되는 `/Adam` 아래에만 손을 댔습니다.

- `Adam/Gr/GrGlbls.HC` — `CGrGlbls` 에 `U16 *text_kr` 추가 (셀당 글리프 번호+1)
- `Adam/Gr/GrInitB.HC` — `gr.text_kr` 할당
- `Adam/Gr/GrScrn.HC` — `GrPutKRCell()` 추가, `GrUpdateTextFG` 디스패치
- `Adam/DolDoc/DocRecalc.HC` — `TextLenStr` → `TextLenStrKR`
- `Adam/FontKR.HC`, `Adam/KRText.HC`, `Adam/FontKR.DAT` — 새 파일
- `Adam/MakeAdam.HC` — `FontKR` 는 `Gr/MakeGr` 앞, `KRText` 는 뒤
- `StartOS.HC` — `FontKRLoad;`
- `HomeSys.HC`, `Adam/ADefine.HC`, `Doc/Start.DD` — 이름/배너

한글 셀은 `gr.text_base[]` 에 매직 문자 `0x01`, `gr.text_kr[]` 에 글리프 번호를 넣고
`GrUpdateTextFG` 가 그 셀만 `GrPutKRCell()` 로 보냅니다. CP949 한 글자는 2바이트라
셀 2칸을 차지하고, 글리프는 앞 칸에 그립니다(둘째 칸은 공백으로 지웁니다).

## 다시 빌드하려면

```bash
# 1) 원본 ISO를 IDE 디스크에 설치해 /root/tos.raw 를 만든 뒤 (2개 파티션, C:/D:)
# 2) 이미지를 마운트하고 소스를 덮어쓴다
bash stage1.sh /tmp/vdisk3          # 원본 .HC 를 풀어서 덮어쓰기 (.Z 삭제)
bash stage2.sh /tmp/vdisk3          # 번역문 트리 덮어쓰기
python3 patch_korean.py /tmp/vdisk3 --template ./templates
python3 applymap_c.py ko503.json /tmp/vdisk3/Once.HC /tmp/vdisk3/HomeSys.HC
# 3) 부팅해서 ISO 굽기
#include "::/Tmp/MakeKRISO";
```

`MakeKRISO.HC` 는 원본 `DoDistro` 와 같지만 `/Distro` 트리를 다시 압축한 뒤 굽습니다.
그래서 ISO가 17 MB 근처로 유지됩니다(`/0000Boot` 는 압축하지 않음).

## 번역 범위

- 부팅 화면에 바로 보이는 것만 번역했습니다.
  `Doc/Start.DD`, `Doc/Tips.DD`(74개 팁), `Doc/Customize.DD`, `Doc/StandBy.DD`,
  `Doc/HelpIndex.DD`, `PersonalMenu.DD`, `Once.HC`, `HomeSys.HC` 등 138개 파일.
- 나머지 문서는 원본 그대로 둡니다. ZealOS 판과 같은 방침입니다.
- 커널 내부 문자열(`Directory of ...`, `AutoComplete is in standby mode`, `MENU`)은
  `Kernel.BIN.C` 안에 있어 번역하지 않았습니다.

## 알려진 한계

- 한글 글리프가 8×8이라 줄 간격이 0입니다. 두 줄이 붙어 보입니다.
- CP949 2바이트 = 셀 2칸이라 한글이 좌우로 벌어져 보입니다(ZealOS 판과 동일).
- 게임과 WiFi는 이 판에서도 빠져 있습니다(유선만).

## 파일

- `templates/FontKR.DAT` — 달무리 8×8, `KRF1` 헤더 + CP949 코드표 + U64 글리프
- `templates/KRText.ZC` — `TextCharKR` / `TextLenStrKR`
- `templates/FontKR.ZC` — 폰트 로더
- `docs/` — 번역된 DolDoc 원본 (CP949)
- `ko503.json` — 부팅 스크립트용 문자열 맵
