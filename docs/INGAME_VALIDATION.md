# 실게임 적용 검증 — 미실행 상태

> 현 단계: **번역 JSON·빌더 정적 검증 완료, 한국어 출력 미검증**.
> 원본 게임·Steam·사용자 설정·세이브에 변경을 가하지 않았습니다.

## 확인된 기술적 제약

Monster Prom 3: Monster Roadtrip Steam 설치본 2026-10-24, build 25955894:

- Unity 2021.3.15f1, Mono / **32-bit x86** EXE. 64-bit 전용 후킹 로더를 쓰면 안 됩니다.
- `CoreParser.ReadLocalizedTextFile()`이
  `StreamingAssets/game_assets/texts/english_events_*.txt` 파일이 존재할 때
  내장 Addressables보다 이를 먼저 읽습니다. 이벤트/선택지/행동 문구까지
  **네 번째 필드만** 변경하고 원본 헤더·메타 데이터를 보존해야 합니다.
- `CoreTextManager.LoadMetatextsFile()`은 `CoreAssetManager.GetTextAsset("english_metatexts")`에
  의존하므로 위의 loose 이벤트 TXT 방식으로는 UI가 번역되지 않습니다.
- 현재 본편에 번들로 포함된 글꼴 6개의 문자 테이블에서 한글 완성형
  11,172자·자모 모두 미지원으로 확인. 따라서 **한글 폰트 주입 없이
  실제 한국어가 보인다고 주장할 수 없습니다.**
- 현재 OS에는 맑은 고딕 및 Noto Sans KR 글꼴이 설치되어 있음(파일은
  저장소·배포 패키지에 포함하지 않음). 실행 시 시스템 글꼴을 불러오는 방식 검토.
- `english_metatexts`에 남아 있는 `Fan Translation Modtool` 메뉴 문자열은
  단지 잔재일 수 있습니다. DLL에서 2편의 `ModTool`/`WorkshopLoader` 구현 클래스는
  확인되지 않았으므로 **공식 번역 모드 사용 가능**이라고 해석하면 안 됩니다.

## 가장 안전한 런타임 적용 설계 (미구현, 미검증)

1. x86 **BepInEx 5 Mono**를 별도 테스트 게임 사본에서만 사용합니다.
2. Harmony가 `BeautifulGlitch.CoreAssetManager.GetTextAsset`의
   `english_metatexts` 결과를 번역된 `TextAsset`으로 치환하여 메뉴와 UI를 번역하도록 설계합니다.
3. `UILabel`(NGUI)과 `UnityEngine.UI.Text`가 한글 문자열을 출력하는 시점에
   `Font.CreateDynamicFontFromOSFont("Malgun Gothic", 24)`로 생성한 한글 폰트를 주입합니다.
   전역 폰트 설정 변경은 UI 레이아웃·줄바꿈 회귀를 유발할 수 있으므로
   동작 보장 전까지 배포하지 않습니다.
4. 이벤트 텍스트는 원본 `ReadLocalizedTextFile`의 loose-file 경로를 사용하고,
   원본 문자열/태그/원문 수치가 정상적으로 들어오는지 확인합니다.

## 합격 기준

1. 원본 게임·저장 데이터 백업을 확보하고 **별도 테스트 사본**에서만 적용합니다.
2. 기본 화면·설정 메뉴의 한국어 UI가 정상 출력되고 글꼴이 깨지지 않습니다.
3. `english_events_default`, `tutorial`, `standard`, `maingame` 이벤트와
   `>choice`·`>action` 문구가 한글로 출력됩니다.
4. 폴리/스콧의 대화, 게임 오버·엔딩 텍스트, 표준 자원 표기,
   `%CURRENTPLAYERNAME%` 등 변수·`[n]` 줄바꿈이 정상 작동합니다.
5. 비번역 키는 기존 영어로 유지되며 게임 저장/불러오기·게임 종료·재시작이 정상입니다.
6. UI 텍스트가 잘리거나 텍스트 박스가 무한 확대되지 않고 폰트 동적 변경
   시 GC/프레임 성능 문제가 없는지 확인합니다.
7. 모든 테스트 부품은 설치 전 복사본 보관 및 완전 제거가 가능해야 합니다.

## 현재 파일

- `build/playtest/game_assets/texts/english_events_*.txt`: 원본 행/메타 구조를
  보존한 이벤트 TXT 테스트 출력물. **실게임 적용 전제 검증은 안 됨**.
- `build/preview/english_metatexts.txt`: UI 한글 문구 검토용. **게임은 이 파일을
  직접 읽지 않음**.

원본 에셋, 게임 복제본, 로더 바이너리, Windows 폰트는 GitHub에 업로드하지 않습니다.
