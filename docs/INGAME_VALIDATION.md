# 실게임 적용 검증 — 메인 메뉴 한국어·2편 글꼴 확인

> **v0.2 발행 결정:** 사용자가 도로 마커 오류를 알려진 이슈로 명시하고
> 최신 수정본을 릴리즈하도록 승인했다. 아래의 이전 보류 기록은 조사 이력이다.
> [v0.2 배포 안내](RELEASE_v0.2.md). 도로 마커 로그가 해결됐다는 의미는 아니며
> 플레이·저장·종료가 이어진 비치명적 이슈로 공개한다.

> **2026-10-25 17:34 KST, 0.1.5 사용자 플레이 후 종료 확인:**
> BepInEx 로그에서 한국어 UI·Jua/GamjaFlower·이름 보호·도로 마커 prefix 로드를 확인했다.
> 완료한 세션은 이벤트 28개 종료, 체크포인트 저장 24회, OnApplicationQuit 및
> 정상 메모리 통계가 기록됐고 Crash!!!/신규 덤프는 없었다.
> 그러나 `Section counter was smaller than 0. Section counter: -1 Count: 6Target point: 4`
> 오류가 1회 재발했다. **0.1.5의 경로 시작 초기화만으로는 해결되지 않았다.**
> 사용자 화면상 문제는 보고되지 않았지만, 요청한 '문제 없으면 발행' 조건이
> 충족되지 않아 v0.2는 발행하지 않았다. 이후 사용자가 다시 실행해 로그가
> 회전됐으므로 완료 세션은 `work/testlogs/Player_015_20261025_173424.log`에 보존했다.
> 기존 `build/releases/`의 Windows ZIP은 15:04 생성된 구형 후보로,
> 최신 종료 충돌 보정과 0.1.5가 포함된 배포본으로 취급하면 안 된다.

> 도로 마커 인덱스 초기화를 보완한 **0.1.5**를 로컬 적용했다.
> [도로 마커 구간 오류 조사](ROADMAP_MOVEMENT_FIX_2026-10-25.md).
> 전체 자동 검사 43개 통과. 기존 종료 충돌 보정은 그대로 유지하며,
> 새 도로 이동 보완은 사용자 실게임 검증이 남아 있다.

> **16:06 KST 사용자 실게임 확인:** 0.1.4 한글 브리지/두 폰트 로드,
> 체크포인트 저장 후 한글 이름 유지, 종료 충돌 없음·신규 덤프 없음 확인.
> 도로 마커 이동 관련 별도 오류 1건은 후속 조사 대상으로 기록했다.
> 상세 근거는 [MonoMod 보정 및 성공 로그](MONO_CORLIB_FIX_2026-10-25.md)를 참고.

> 최신 상태: **0.1.4 + 로컬 MonoMod 구조체 위치 보정**.
> [종료 충돌 원인 확정 및 영어 UI 복구](MONO_CORLIB_FIX_2026-10-25.md).
> 0.1.3의 Cecil 후보는 브리지 로딩 실패로 폐기했고 auto로 복구했다.
> 독립 x86 Mono 시험에서 원본 포인터 손상/충돌 및 보정 후 정상 종료를
> 재현했다. 전체 자동 검사 42개 통과. 사용자 실게임 확인이 남아 있다.

> 최신 로컬 후보는 **0.1.3**이다.
> [종료 충돌 및 플레이 중 스탯 오류 조사](RUNTIME_CRASH_AUDIT_2026-10-25.md)를 참고.
> 스탯 토큰 86행의 추가 경계 누락을 수정했고 전체 게임 정규식 검사를 통과했다.
> 종료 충돌에는 가드와 Cecil 생성기 후보를 적용했으며 사용자 실행 검증이 남아 있다.

> 후속 조사: [UI 누락 및 종료 오류 조사](UI_RUNTIME_AUDIT.md).
> 브리지 0.1.1에 로딩·스탯 이름 표시 경로 보완을 추가했다.
> 최신 두 게임 로그에서 게임 진입과 종료 중 충돌을 확인했으며,
> 수정본 실행 테스트는 사용자가 직접 진행한다.

> **2026-10-24 Steam 실게임 테스트:** 한글 메인 메뉴, `english_metatexts`
> 런타임 교체, Jua 헤더/감자꽃 본문을 화면·BepInEx 로그로 확인했습니다.
> 원본 DLL/AssetBundle 및 사용자 세이브는 변경하지 않았고, 별도 로더 파일을
> 추가했습니다. **이벤트 대사 전체·선택지·게임 저장 검증은 미완입니다.**
> 2026-10-25 현재 번역 후보 **30,255/30,255개(100.00%)**, 본편은
> **18,119/18,119개**로 정적 번역/빌드 검증을 완료했습니다. UI 미리보기는 2,871개 키로 갱신됐지만,
> 마지막 실제 게임 로그는 이전 195개 키 미리보기를 사용한 세션입니다.
> **최신 2,871개 UI와 27,384개 이벤트 TXT·신형 브리지는 로컬 설치를 새로 완료했지만**,
> 아직 새 게임 세션에서 화면·진행·저장·불러오기를 확인하지 않았습니다.

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
  **Gamja Flower**가 지정돼 있음. 현재 번역 한글 음절 1,468종은 두 폰트의
  글리프 감사에서 누락 0개로 확인됐습니다. 다만 Jua는
  전체 한글 완성형의 일부만 지원함.
  [로컬 추출·문자 지원 감사](FONT_REUSE.md)를 참조.
- `english_metatexts`에 남아 있는 `Fan Translation Modtool` 메뉴 문자열은
  단지 잔재일 수 있습니다. DLL에서 2편의 `ModTool`/`WorkshopLoader` 구현 클래스는
  확인되지 않았으므로 **공식 번역 모드 사용 가능**이라고 해석하면 안 됩니다.

## 런타임 적용 설계 (소스·컴파일·메뉴 실행 확인)

1. **BepInEx 5 Mono x86**를 사용자 요청으로 설치했습니다. 원본 DLL과
   Unity 번들은 그대로 두었습니다. 2026-10-25에는 브리지를 배포용 상대 경로로
   수정·재컴파일하고 설치 기록의 기존 파일 33개를 로컬에 백업·정상 제거한 뒤
   최신 이벤트/메타텍스트/브리지 파일 **35개**를 새로 설치했습니다. 설치 대상 해시
   검증 및 원본 DLL·Unity 번들의 기존 SHA 일치 확인까지 통과했습니다.
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
   **통과**: `work/install/installed_files.json`에 설치 대상 35개와 원본 SHA 보존.
   이전 33개는 `work/install/backup_before_translation_100pct/`에 로컬 백업했습니다.
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
  보존한 이벤트 TXT 테스트 출력물. 최신 출력물을 로컬 게임에 설치했으나
  **최신 빌드 기준 실제 화면·이벤트 분기 검증은 아직 안 됨**.
- `build/preview/english_metatexts.txt`: UI 2,871개 키 한글 문구 검토용.
  게임 자체 로더는 읽지 않습니다. 이전 미리보기는 BepInEx 브리지 후킹으로
  적용을 확인했습니다. 현재 파일을 신형 브리지와 함께 설치했지만 새 게임
  세션에서 실제 로드했는지는 미확인입니다.
- `src/RoadtripKoreanFontBridge/`: 3편용 선택형 BepInEx Mono x86 폰트/UI
  브리지 **소스**. 새 빌드의 기본 미리보기/선택 폰트 경로는 플러그인 폴더 기준이며,
  컴파일된 DLL은 Git에서 제외됩니다. 현재 로컬 설치본은 최신 컴파일된 DLL입니다.
- `build/fontbundles/roadtrip_korean_fonts.bundle`: 2편 번들을 로컬에서
  재구성해 생성·실게임 로딩에 성공한 **Git 제외 테스트 자산**.
- `scripts/install_local_playtest.ps1`, `uninstall_local_playtest.ps1`:
  해시 검증 후 신규 설치 파일만 추가·제거하는 스크립트.
- **미지원 경로:** 게임 일부 `TextMeshPro` 위젯은 기존 플러그인이 다루지 않음.
  특수 공지/배너 등에 미번역 또는 글꼴 누락 가능, 추가 테스트 필요.

원본 에셋, 게임 복제본, 로더 바이너리, Windows 폰트는 GitHub에 업로드하지 않습니다.
