# 실게임 적용 검증 — 메인 메뉴 한국어·2편 글꼴 확인

> **2026-10-24 Steam 실게임 테스트:** 한글 메인 메뉴, `english_metatexts`
> 런타임 교체, Jua 헤더/감자꽃 본문을 화면·BepInEx 로그로 확인했습니다.
> 원본 DLL/AssetBundle 및 사용자 세이브는 변경하지 않았고, 별도 로더 파일을
> 추가했습니다. **이벤트 대사 전체·선택지·게임 저장 검증은 미완입니다.**
> 이후 번역 작업은 총 7,664개까지 확장했으나, 새 이벤트 출력물은
> **작업 폴더에만 생성**되었으며 기존 게임 설치본에 재적용하지 않았습니다.

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
- 2편 설치본에 실제 포함된 `fontset_korean` 프로필에는 제목용 **Jua**, 본문용
  **Gamja Flower**가 지정돼 있음. 최초 실게임 번역 당시 한글 음절 943종을 지원했고,
  이후 번역본의 1,235종도 정적 글리프 검사에서 누락 없이 지원하지만,
  두 글꼴 중 Jua는 전체 한글 완성형의 일부만 지원함.
  [로컬 추출·문자 지원 감사](FONT_REUSE.md)를 참조.
- `english_metatexts`에 남아 있는 `Fan Translation Modtool` 메뉴 문자열은
  단지 잔재일 수 있습니다. DLL에서 2편의 `ModTool`/`WorkshopLoader` 구현 클래스는
  확인되지 않았으므로 **공식 번역 모드 사용 가능**이라고 해석하면 안 됩니다.

## 런타임 적용 설계 (소스·컴파일·메뉴 실행 확인)

1. **BepInEx 5 Mono x86**를 사용자 요청으로 설치했습니다. 원본 DLL과
   Unity 번들은 그대로 두고 신규 파일 33개만 추가했습니다.
2. Harmony가 `BeautifulGlitch.CoreAssetManager.GetTextAsset`의
   `english_metatexts` 결과를 번역된 `TextAsset`으로 치환하여 메뉴와 UI를 번역하도록 설계합니다.
3. `UILabel`(NGUI)과 `UnityEngine.UI.Text`가 한글 문자열을 출력하는 시점에
   가능하면 2편의 **Jua / Gamja Flower**를 각각 제목/본문용으로 주입합니다.
   구형 Unity AssetBundle 직접 읽기가 실패한다면
   `Font.CreateDynamicFontFromOSFont("Malgun Gothic", 24)`로 생성한
   한글 폰트를 대체 사용합니다.
   전역 폰트 설정 변경은 UI 레이아웃·줄바꿈 회귀를 유발할 수 있으므로
   동작 보장 전까지 배포하지 않습니다.
4. 이벤트 텍스트는 원본 `ReadLocalizedTextFile`의 loose-file 경로를 사용하고,
   원본 문자열/태그/원문 수치가 정상적으로 들어오는지 확인합니다.

`src/RoadtripKoreanFontBridge/`는 .NET Framework 4.7.2/x86으로
BepInEx5+Harmony 및 3편 원본 DLL 참조를 이용해 **경고 0·오류 0으로 컴파일**했습니다.
초기 실행에서는 기존 2편 AssetBundle에서 폰트 루트가 노출되지 않아 맑은 고딕으로
표시됐지만, `scripts/expose_camp_fonts.py`가 원본을 건드리지 않고 만든 로컬
번들에 Jua/GamjaFlower 두 개를 루트 자산으로 노출하자 게임 로그에
**`LoadAllAssets<Font>() returned 2 Font asset(s)`**, `Selected header font: 'Jua'`,
`Selected body font: 'GamjaFlower'`가 출력됐습니다. 게임 제목 메뉴의 글꼴
변화도 스크린샷(`work/testlogs/roadtrip_original_camp_fonts.jpg`)으로 확인했습니다.

## 합격 기준

1. 원본 파일의 SHA256을 기록하고 새로 추가한 파일은 제거 가능해야 합니다.
   **통과**: `work/install/installed_files.json`에 설치 대상 33개와 원본 SHA 보존.
2. 기본 화면·설정 메뉴의 한국어 UI가 정상 출력되고 글꼴이 깨지지 않습니다.
   **메인 메뉴 확인**, 설정 하위 메뉴는 미확인.
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
- `build/preview/english_metatexts.txt`: UI 한글 문구 검토용.
  게임 자체 로더는 읽지 않으나 **BepInEx 브리지의 후킹으로 적용 확인**.
- `src/RoadtripKoreanFontBridge/`: 3편용 선택형 BepInEx Mono x86 폰트/UI
  브리지 **소스**. 빌드된 DLL은 Git에서 제외되며 로컬 게임에만 설치됨.
- `build/fontbundles/roadtrip_korean_fonts.bundle`: 2편 번들을 로컬에서
  재구성해 생성·실게임 로딩에 성공한 **Git 제외 테스트 자산**.
- `scripts/install_local_playtest.ps1`, `uninstall_local_playtest.ps1`:
  해시 검증 후 신규 설치 파일만 추가·제거하는 스크립트.
- **미지원 경로:** 게임 일부 `TextMeshPro` 위젯은 기존 플러그인이 다루지 않음.
  특수 공지/배너 등에 미번역 또는 글꼴 누락 가능, 추가 테스트 필요.

원본 에셋, 게임 복제본, 로더 바이너리, Windows 폰트는 GitHub에 업로드하지 않습니다.
