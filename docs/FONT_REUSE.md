# 2편 한글 글꼴 재사용 조사 및 로컬 테스트 준비

**현재 상태:** 사용자 PC에 설치된 *Monster Prom 2: Monster Camp*에서
한국어용 글꼴 두 개를 읽기 전용으로 확인했고, *Monster Roadtrip* 3편의
로컬 작업 폴더로만 추출했습니다. **3편 실게임 출력은 아직 확인하지 않았습니다.**

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
- 현재 3편 한국어 번역의 한글 완성형 고유 음절 **943종은 두 폰트에서 모두 지원**.
  그러나 향후 추가 번역에서 주아가 지원하지 않는 글자가 생길 수 있으므로
  빌드 시 글리프 검사를 반복하고 해당 문자열은 감자꽃 등 대체 폰트로 처리해야 합니다.
- 현재 번역에서 **주아는 `®`(2회), `《`, `》`(각 1회)**,
  **감자꽃은 `®`(2회)** 문자를 표시하지 못합니다. OS 폰트 대체
  또는 개별 문구 조정이 필요합니다. 이후 추가 번역은 검사 재실행 권장.

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

가장 재현성 높은 장기 방식은 준비된 OFL TTF 두 개를
**Unity 2021.3.15f1용 개별 Font 루트 AssetBundle**로 로컬에서 재패키징한 뒤
3편의 선택형 x86 Mono 플러그인으로 불러오는 것입니다. 이는 Unity Editor가
별도로 필요하며 현재 리포지토리의 폰트 준비 단계만으로는 이루어지지 않습니다.

이를 위한 **에디터 빌드 소스**도 준비해 두었습니다.

```powershell
cd D:\Codex_Trans\Monster-Prom-3-KR
.\scripts\build_camp_font_bundle.ps1 -UnityEditorPath 'C:\Program Files\Unity\Hub\Editor\2021.3.15f1\Editor\Unity.exe'
```

스크립트는 버전을 먼저 검사하고, 사용자 PC의 `work/fonts/`에 추출한
폰트를 `work/unity_font_project/` 안에서만 복사·가공해
`build/fontbundles/roadtrip_korean_fonts.bundle`을 생성하도록 설계했습니다.
**현재 PC에는 Unity 6000 에디터만 확인되고 Unity 2021.3.15f1 에디터는
없으므로 실제 에셋 번들 빌드는 실행하지 않았습니다.** 이는 향후 설치 후
검증할 수 있는 레시피일 뿐, 완성된 바이너리가 아닙니다.

구현 우선순위는 3편 전용 런타임 폰트 브리지에서 `Jua`를 헤더용,
`GamjaFlower`를 본문용으로 할당하는 것입니다. 직접 번들 로딩이 안 되면
별도의 OS 폰트 등록/적합한 Unity2021 번들 제작이 필요합니다. 그전까지는
시스템에 이미 설치된 맑은 고딕이나 노토 산스 KR을 **임시 대체 글꼴**로
사용할 수 있지만 2편의 글꼴 디자인과는 다릅니다. 단순히 로컬 TTF를
복사했다고 `Font.CreateDynamicFontFromOSFont`가 자동으로 읽지는 않습니다.
원본 2편 파일을 게임 폴더에 덮어쓰지 않습니다.

참고: <https://docs.unity.com/en-us/engine/6000.3/manual/assets-and-media/assets-managing-runtime/assetbundles-section/asset-bundles-intro>

## 배포 기준

글꼴 파일은 이 저장소에 넣거나 GitHub에 업로드하지 않습니다.
장차 글꼴을 별도로 재배포한다면 해당 폰트의 **SIL OFL 원문과 저작권 고지**를
재배포물에 포함하는 방식으로 별도 검토해야 합니다. 현재는 개발 PC에서
정품 2편 설치본을 읽는 테스트용 자산으로만 사용합니다.
