# 2편 한글 글꼴 재사용 — 3편 실게임 적용 확인

**2026-10-24 실제 적용 확인:** 사용자 PC의 *Monster Prom 2: Monster Camp*에서
주아·감자꽃을 읽기 전용으로 추출해 *Monster Roadtrip* 3편에 연결했습니다.
BepInEx 로그의 폰트 선택 성공과 한글 메인 메뉴 스크린샷을 확인했습니다.
**추가 이벤트 대사·전체 UI 회귀 검증은 미완**입니다.

## 실제 2편 글꼴 프로필

2편의 `MonsterCamp_Data/StreamingAssets/aa/StandaloneWindows/` 아래
`profilesfontsets_assets_all_79f49ff1b358585c59c1388d6a773d92.bundle`를
UnityPy로 읽었습니다. `fontset_korean` 프로필의 레퍼런스는 다음과 같습니다.

| 용도 | 2편 지정 Unity Font | 실제 폰트 패밀리 | 한글 완성형 지원 |
|---|---|---|---|
| 제목/헤더 | `Jua` | Jua | **2,367 / 11,172** |
| 본문/대사 | `GamjaFlower` | Gamja Flower | **11,172 / 11,172** |

- `fontset_korean.unityUiHeaderFont` → `Jua`
- `fontset_korean.unityUiBodyFont` → `GamjaFlower`
- 두 폰트의 `name` 메타데이터에 **SIL Open Font License 1.1** 표기가 확인됨.
- 3편 한글화 최초 인게임 검증의 고유 음절 **943종**, 이후 추가 번역을 포함한
  **2026-10-25 현재 1,334종 모두** 두 폰트에서 지원함을 재검사했습니다.
  그러나 향후 추가 번역에서 주아가 지원하지 않는 글자가 생길 수 있으므로
  빌드 시 글리프 검사를 반복하고 해당 문자열은 감자꽃 등 대체 폰트로 처리해야 합니다.
- 최신 `prepare_camp_fonts.py --audit-only` 결과, 현재 번역에 쓰인 한글 완성형
  **1,334종은 두 폰트 모두 누락 없이 지원**합니다. 한글 외 유니코드 중 미지원 문자는
  주아 31종, 감자꽃 21종으로 집계됐습니다. 실제 화면에서 특수문자 대체가 필요한지
  확인하고, 신규 번역 이후에는 감사를 재실행합니다.

## 개발 PC에서만 준비

```powershell
cd D:\Codex_Trans\Monster-Prom-3-KR
python -m pip install UnityPy fonttools
python -X utf8 scripts\prepare_camp_fonts.py
# 원본 폰트 메타데이터만 검사하고 추출하지 않으려면
python -X utf8 scripts\prepare_camp_fonts.py --audit-only
```

이 과정은 2편에 설치된 원본 번들에서 추출한 Jua/GamjaFlower 폰트와
그 검사 결과를 **gitignored `work/fonts/`** 에만 저장합니다.
`git ls-files` 결과에 폰트 바이너리가 포함되지 않도록 해야 합니다.
**2편 설치본, 3편 설치본, 시스템 폰트, Steam 및 사용자 세이브는 수정하지 않습니다.**
게임이 설치되지 않은 다른 PC에서는 이 추출 단계가 불가능할 수 있습니다.

## 3편 런타임 연결이 별도로 필요한 이유

3편의 Unity 2021.3 Mono x86에는 한글 폰트 프로필이 없고,
3편에 포함된 기본 폰트 6종의 한글 완성형 커버리지는 0입니다.
2편 Unity 2019.4의 `fontset_korean` 전체 자산을 그대로 복사해도
3편의 `LanguageProfile`과 자동 연결되지 않습니다.

원본 AssetBundle을 *더 새로운 Unity*에서 로딩하는 것은 Unity에서
보통 허용하는 방향이지만, 구버전의 스크립트 객체 타입/직렬화 구조에
영향을 받을 수 있습니다. 추가 조사에서 2편 번들의 `m_Container`에는
오직 여덟 개의 `fontset_*.asset` 루트만 등록되어 있으며 `Jua`와
`GamjaFlower`는 `fontset_korean`이 참조하는 의존 오브젝트로 확인했습니다.
더구나 `FontSetProfile` 클래스는 3편의 C# DLL에 없습니다.
따라서 **2편 번들에서 `LoadAllAssets<Font>()`만 호출해서 글꼴 두 개를
얻는 방식은 성공을 보장할 수 없습니다.**

## Unity Editor 없이 기존 번들에서 Font 루트 노출 — 실게임 테스트 통과

`scripts/expose_camp_fonts.py`는 2편 원본 번들의 AssetBundle `m_Container`에
이미 번들 안에 존재하던 `Jua`와 `GamjaFlower` Font 오브젝트의 **루트 레퍼런스
두 개만 추가**합니다. 해당 폰트의 `PathID`, `fontset_korean`에서 사용한
의존 자산 `preloadIndex`/`preloadSize`를 그대로 유지하며, UnityPy가 로컬
복제본을 LZ4 방식으로 직렬화합니다. **2편 원본 설치 파일은 수정하지 않습니다.**

```powershell
cd D:\Codex_Trans\Monster-Prom-3-KR
python -X utf8 scripts\prepare_camp_fonts.py
python -X utf8 scripts\expose_camp_fonts.py
```

출력은 Git 제외 `build/fontbundles/roadtrip_korean_fonts.bundle`입니다. 실제
3편 Unity 2021.3.15f1 게임에서 `LoadAllAssets<Font>()`가 **2개를 반환**했고,
최초 실게임 로딩 당시 두 글꼴 모두 한글 **943종** 검사에 합격했습니다.
이후 추가 번역본의 **1,334종**도 `prepare_camp_fonts.py --audit-only`와
자동 테스트에서 두 폰트 모두 누락 0개로 확인했습니다(후속 게임 실행 미검증).

기본 메뉴 스크린샷에서는 주아 스타일의 한글 글꼴이 보였고, 로그에서
`Selected header font: 'Jua'` 및 `Selected body font: 'GamjaFlower'`가 확인됐습니다.
이 우회법은 **테스트한 현재 2편·3편 버전에 한해** 검증했으며 향후 게임 업데이트
시 재검증이 필요합니다. 출력 번들은 2편 게임 자산을 포함하므로 **절대 공개
저장소나 릴리스 파일에 업로드하지 않습니다.**

### 대안: Unity 2021 Editor를 이용한 새 번들 제작

기존 버전 자산과의 미래 호환성 문제가 생기면, 준비된 OFL TTF 두 개를
Unity 2021.3.15f1용 개별 Font 루트 AssetBundle로 처음부터 재패키징하는
방식을 사용할 수 있습니다. 이는 해당 Unity Editor가 있어야 합니다.

이를 위한 **에디터 빌드 소스**도 준비해 두었습니다.

```powershell
cd D:\Codex_Trans\Monster-Prom-3-KR
.\scripts\build_camp_font_bundle.ps1 -UnityEditorPath 'C:\Program Files\Unity\Hub\Editor\2021.3.15f1\Editor\Unity.exe'
```

스크립트는 버전을 먼저 검사하고, 사용자 PC의 `work/fonts/`에 추출한
폰트를 `work/unity_font_project/` 안에서만 복사·가공해
`build/fontbundles/roadtrip_korean_fonts.bundle`을 생성하도록 설계했습니다.
현재 PC에는 Unity 6000 에디터만 확인되므로 이 **대체 빌드 경로**는 실행하지
않았습니다. 위 UnityPy 방식으로 이미 글꼴 로딩 성공을 확인했습니다.

3편 런타임 브리지는 우선 재구성한 번들에서 주아/감자꽃을 사용합니다. 실패하면
Windows 프로세스 전용 폰트 등록을 시도하지만, 실제 게임 테스트에서는
Unity가 사설 등록을 OS 글꼴 목록에서 찾지 못했습니다. 이후 2편 원본 번들
직접 접근도 실패해 최종적으로 맑은 고딕 대체 표시가 성공한 바 있습니다.
실제 재구성 번들이 있을 때에는 **맑은 고딕으로 대체하지 않고 주아/감자꽃을
사용**합니다. 원본 2편 파일을 게임 폴더에 덮어쓰지 않습니다.

참고: <https://docs.unity.com/en-us/engine/6000.3/manual/assets-and-media/assets-managing-runtime/assetbundles-section/asset-bundles-intro>

## 배포 기준

글꼴 파일은 이 저장소에 넣거나 GitHub에 업로드하지 않습니다.
장차 글꼴을 별도로 재배포한다면 해당 폰트의 **SIL OFL 원문과 저작권 고지**를
재배포물에 포함하는 방식으로 별도 검토해야 합니다. 현재는 개발 PC에서
정품 2편 설치본을 읽는 테스트용 자산으로만 사용합니다.
