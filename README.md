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
- 한국어 글꼴·동적 태그·줄바꿈·게임 실행 적용 여부는 **아직 검증하지 않았습니다**.

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
  `build/preview/english_metatexts.txt`에 생성. **이 파일은 아직 게임에 적용되지 않습니다.**

### 실게임 테스트 전 주의

현재 프로젝트에서 게임 폴더로 파일을 자동 복사하지 않습니다. 테스트가 승인되면
`build/playtest/game_assets/texts/english_events_*.txt`를 게임 설치 경로
`MonsterRoadtrip_Data/StreamingAssets/game_assets/texts/` 아래에 배치하고
게임 언어를 영어로 유지해야 해당 오버라이드 탐색 경로를 사용합니다.
하지만 게임 실행에서 한글 글꼴과 실제 출력이 검증되기 전에는
**완성된 설치 패치라고 배포하지 않습니다.** 게임 파일을 직접 덮어쓰거나 수정하지 마세요.

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
컴파일은 되었지만 실게임 실행·한글 출력·2019→2021 번들 호환성을
아직 검증하지 않았으므로 배포 가능한 완성 패치로 취급하면 안 됩니다.
