# Monster Prom 3: Monster Roadtrip — Korean translation project

한국어 패치 **초기 작업본**입니다. 2편 *Monster Camp*의 완성 파일이나 1편 패치를
3편에 그대로 설치하면 안 됩니다. 게임 원본·저장 파일과 기존 한글화 프로젝트는 변경하지 않습니다.

## 2026-10-24 구조 조사 및 번역 착수

- 검증 대상: Steam `Monster Prom 3 - Monster Roadtrip`, build `25955894`.
- Unity/Mono, `Assembly-CSharp.dll`, Addressables TextAsset 구조를 읽기 전용으로 확인.
- 기본 설치본의 3개 언어 프로필: `english`, `schinese`, `spanish`. **한국어 프로필 없음**.
  기존 프로필의 `languageType` 값은 모두 `English`; 실제 번역 TextAsset은 영어 12개만 존재.
- `BeautifulGlitch.CoreParser.ReadLocalizedTextFile()`은
  `<Game>_Data/StreamingAssets/game_assets/texts/<language>_<file>.txt`가 존재하면
  Addressables TextAsset보다 **먼저** 읽습니다. 이것은 대사용 외부 텍스트 패치의 근거입니다.
- 메타텍스트는 별개: `BeautifulGlitch.CoreTextManager.LoadMetatextsFile()`이
  `CoreAssetManager.GetTextAsset("english_metatexts")`를 통해 Addressables에서 읽습니다.
  외부 TXT를 같은 경로에 두어도 UI가 자동으로 번역되지 않습니다.
- 2편과 달리 팬 번역용 ModTool/Workshop 로딩 클래스는 해당 설치본 DLL에서 확인되지 않았습니다.
- 2026-10-24 실제 Steam 실행에서 **메인 메뉴 한국어 출력**과 2편의
  **Jua(주아)·Gamja Flower(감자꽃)** 로딩을 확인했습니다. 대사 전체·분기·저장
  및 TextMeshPro 화면까지 검증한 것은 아닙니다.

## 원문 분량

| 구분 | 초기 추출 수 |
| --- | ---: |
| 영어 `TextAsset` | 12 |
| 이벤트 정의 | 1,509 |
| 일반 이벤트 대사 행 | 26,234 |
| 선택지 `>choice`의 네 번째 필드 | 777 |
| 행동 문구 `>action`의 네 번째 필드 | 373 |
| 메타텍스트 키/값 | 2,871 |
| **총 번역 후보** | **30,255** |

원본 탭 구분 데이터에서 일반 대사·선택지·행동 문구를 구분해 센 **초기 후보**이며
최종 번역 대상의 정확한 수와 다를 수 있습니다.

## 작업 환경 및 빌드

의존성: Python 3, [`UnityPy`](https://github.com/K0lb3/UnityPy),
선택적인 폰트 검사 도구 [`fonttools`](https://github.com/fonttools/fonttools).

```powershell
cd D:\Codex_Trans\Monster-Prom-3-KR
python -X utf8 scripts\extract_assets.py
python -X utf8 scripts\build_playtest.py
python -X utf8 scripts\build_ui_preview.py
python -X utf8 scripts\prepare_camp_fonts.py
python -X utf8 scripts\expose_camp_fonts.py
python -X utf8 scripts\audit_progress.py
python -X utf8 -m unittest discover -s tests -v
```

추출 결과는 `work/source`와 `work/catalog.jsonl`, `work/source_manifest.json`에
저장됩니다. `work/`와 `build/`는 `.gitignore` 대상으로, 게임 소유의 원문을 Git에 넣지 않습니다.

### 번역 데이터

- `translations/english_events_*.json`: 기존 이벤트 이름/실제 파일 행 번호와
  원문 SHA-256에 묶은 한국어 **대사 필드**만 저장. 이벤트 명령·분기·화자·표정은 원형 보존.
- `translations/english_metatexts_ko.json`: UI 문자열 키와 한국어 번역.
- `scripts/build_playtest.py`: 원문 해시·이벤트명·대사 해시·원본 제어 태그·숫자·행수를
  검증한 후 실제 게임이 읽을 **영어 슬롯 오버라이드 파일**을 `build/playtest/game_assets/texts/`에 생성.
- `scripts/build_ui_preview.py`: 구조를 유지한 UI 번역 검토본을
  `build/preview/english_metatexts.txt`에 생성. 3편 전용 런타임 브리지로
  **영어 UI 슬롯에 실제 적용되는 것**을 게임 실행 및 스크린샷으로 확인했습니다.

### 설치·제거 및 실게임 테스트

테스트 설치는 `scripts/install_local_playtest.ps1`를 통해 수행합니다.
검증된 x86 BepInEx와 선택형 브리지 DLL, 영어 슬롯 이벤트 TXT 11개만
**새 파일로 추가**하며 기존 파일과 충돌하면 설치를 거부합니다. 설치된
파일별 SHA256은 `work/install/installed_files.json`에 기록합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_local_playtest.ps1
# 게임을 종료한 뒤 설치 제거
powershell -ExecutionPolicy Bypass -File scripts\uninstall_local_playtest.ps1
```

게임은 Steam에서 실행하고 언어를 **영어**로 유지합니다. 게임의 원본 DLL,
원본 AssetBundle 및 기존 저장 데이터는 변경하지 않습니다.
2026-10-24 기준 **총 30,255개 후보 중 11,028개(36.45%)**를 한국어로 번역한
진행 중인 프로젝트이므로 **완역판으로 배포하지 않습니다.**
내역은 [번역 진행 보고](docs/TRANSLATION_PROGRESS.md)를 참고하세요.

게임 설치본에서 확인된 한글 메인 메뉴·글꼴 테스트는 **이전 1,081개 번역 시점**에
수행됐습니다. 이후 추가 번역은 소스/빌드/문자 검증을 통과했지만, 사용자의
설치 게임에 새 이벤트 TXT를 자동 덮어쓰지 않았으므로 전체 인게임 QA는 별도입니다.

## 번역 원칙

게임의 원본 이벤트/분기·변수 `%...%`, UI 태그 `[...]`, `<...>`와
아라비아 숫자·능력치 변동은 정확히 보존합니다. 기존 화자별 말투와
원작 특유의 저속한 농담, 메타 개그, 성적 농담을 현지화합니다.
번역되지 않은 행은 테스트 출력에서 원문 그대로 유지하며,
검증되지 않은 문자열을 임의로 채워 넣거나 새 게임 동작을 생성하지 않습니다.

테스트 빌드는 항상 사용자 로컬 원본에서 재생성할 수 있게 설계합니다.

실게임 구동 확인·한글 글꼴/메뉴 주입과 회귀 테스트는
[`docs/INGAME_VALIDATION.md`](docs/INGAME_VALIDATION.md)에 별도로 추적합니다.
2편 한국어용 **Jua / Gamja Flower**를 3편에 재사용하는 로컬 감사/추출 절차는
[`docs/FONT_REUSE.md`](docs/FONT_REUSE.md)에 기록했습니다.

선택형 3편용 폰트/UI 런타임 브리지 **소스**는
[`src/RoadtripKoreanFontBridge/`](src/RoadtripKoreanFontBridge/)에 있습니다.
컴파일뿐 아니라 실제 게임 메인 메뉴 한글 출력과 폰트 로딩까지 확인했습니다.
향후 한국어 이벤트·선택지와 TextMeshPro 등 추가 화면의 종합 QA는 남아 있습니다.
