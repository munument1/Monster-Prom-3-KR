# Monster Roadtrip 한국어 패치 v0.2

## 설치 — Windows

1. 게임을 종료하고 **`Monster-Roadtrip-KR-v0.2-Windows-DragDrop.zip`**을 받아 압축을 풉니다.
2. Steam에서 게임 우클릭 → **관리 → 로컬 파일 탐색**을 누릅니다.
   압축을 푼 폴더 **안의 내용물 전부**를 열린 게임 폴더에 복사합니다.
   같은 파일이 있으면 덮어씁니다. `MonsterRoadtrip.exe` 옆에 `winhttp.dll`이 있으면 맞는 위치입니다.
3. 게임을 실행합니다. 게임 언어는 **English**로 둡니다.

**주아·감자꽃 폰트 포함. 별도의 글꼴 설치나 명령어 실행은 필요 없습니다.**
기존 세이브는 그대로 사용합니다. 다른 모드가 설치돼 있다면 겹치는 파일은 먼저 백업하세요.

검증 대상: Steam build 25955894, Windows x86. Linux/Steam Deck은 검증하지 않았습니다.

---

이벤트 대사·선택지·행동 27,384개와 UI 2,871개, 총 30,255개 번역 후보를 포함합니다.
전체 분기와 엔딩을 실제로 모두 플레이한 것은 아니며 번역·표시 검수는 계속 필요합니다.

## 수정 사항

- 한글 주인공 이름을 체크포인트에 저장할 때 `???`로 손실되던 ASCII XML 쓰기를 보완했습니다.
  이미 `???`로 저장된 이름을 배포 패치가 자동 복구하지는 않습니다.
- 시작 시 로딩 문구와 플레이 중 우측 상단 스탯 이름을 한국어 UI로 연결했습니다.
- 한국어 조사와 붙은 스탯 효과 토큰의 경계를 보완했습니다.
- 검증된 Windows x86 Mono 빌드에서 종료 시 충돌을 일으키던 MonoMod 메모리 위치 계산을
  보정했습니다. **다른 Mono 버전·64비트·Linux에 이 보정 DLL을 적용하지 마세요.**
- 새 도로 이동 시작 시 구간 인덱스를 초기화하는 보완을 포함합니다.
  이 보완으로 도로 마커 오류 전체가 해결된 것은 아닙니다.

배포 버전은 v0.2이며 내부 브리지 버전은 0.1.5입니다.

## 알려진 이슈

- **도로 마커:** 간헐적으로 `Section counter was smaller than 0 ... -1` 로그가 남습니다.
  0.1.5에서도 1회 재발했으며 이후 도착·이벤트 진행·저장·종료는 정상적으로 이어졌습니다.
  원본 게임의 이동 처리에서 발생하며 한글 패치와 무관한지는 완전히 분리 재현하지 않았습니다.
  사용자 요청에 따라 이 비치명적 오류를 알려진 이슈로 공개하고 발행합니다.
- 모든 이벤트/엔딩, TextMeshPro 전용 UI, 화면 비율별 줄바꿈을 전수 확인하지 않았습니다.
- `evilmenu`·`diner_doom` 등 특정 이벤트 경로의 과거 오류가 이번 플레이로 전부
  재검증된 것은 아닙니다. 모든 경로의 무오류를 보장하지 않습니다.

## 검증

2026-10-25 17:34 KST에 끝난 사용자 세션에서 브리지 0.1.5, 한국어 UI,
주아·감자꽃 로드, 이벤트 28개 종료와 체크포인트 저장 24회를 확인했습니다.
OnApplicationQuit 이후 정상 종료가 기록됐고 새 충돌 덤프는 없었습니다.
Release x86 빌드 경고/오류 0개, 자동 검사 43개, 이벤트 11개 구조 독립 검사와
번역 불변 델타 검사를 통과했습니다. 사용자 세이브는 배포 파일에 포함하지 않습니다.

## 다른 다운로드 / 문제가 있을 때

- `manual-overwrite.zip`: 이벤트 TXT 11개만 담은 보조 파일입니다. UI·폰트·런타임 수정은 없습니다.
  일반 Windows 사용자는 위의 **Windows-DragDrop.zip 하나만** 받으세요.
- `source-testkit.zip`: 개발/재현용 소스와 번역 데이터입니다. 일반 설치에는 필요 없습니다.
- 설치가 안 되거나 다른 게임 버전이라면 동봉한 `VERIFY-WINDOWS.ps1`로 빌드를 검사할 수 있습니다.
  일반 설치에 필수인 단계는 아닙니다.
- 이전 테스트에서 BepInEx 설정을 직접 바꿨다면 `BepInEx/config/BepInEx.cfg`의
  `[Preloader]` 항목을 `HarmonyBackend = auto`로 되돌리세요.
- 제거는 ZIP 파일 목록을 기준으로 추가한 파일만 지우고 기존 파일은 백업에서 복원합니다.
  세이브 폴더나 게임 원본 DLL/번들은 지우지 마세요.

## 폰트 동봉 안내

첫 v0.2 ZIP에서 빠졌던 **주아(Jua)·감자꽃(Gamja Flower)**을 공개 OFL 원본으로 추가했습니다.
게임 프로필·스크립트·그림·다른 글꼴이 섞인 기존 게임 번들은 동봉하지 않습니다.
이제 Windows ZIP에 두 폰트만을 위한 최소 컨테이너와 저작권/OFL 원문이 들어 있습니다.
[공개 원본 및 파일 해시](https://github.com/munument1/Monster-Prom-3-KR/blob/main/docs/PUBLIC_FONT_SOURCES.json).

이 패키지 갱신에서 브리지 0.1.5 및 종료 충돌 보정 DLL은 바꾸지 않았습니다.
이번 갱신의 자동 검사 **44개**를 통과했습니다. 새 공개 폰트 컨테이너는
구조·참조·현재 번역 한글 1,468종의 글리프를 자동 검사했습니다.
기존 사용자 플레이 검증은 기존 로컬 번들 환경에서 수행했으며,
**새 컨테이너를 이용한 실제 게임 화면은 추가 확인이 필요합니다.**

## 제3자 구성 요소

Windows 로더는 BepInEx 5.4.23.2 x86과 그 포함 구성 요소를 사용합니다.
MonoMod.Utils.dll에는 이 게임 빌드만을 위한 로컬 보정을 적용했습니다.
보정 소스는 `scripts/build_mono_corlib_fix.ps1`에 공개합니다.

- [BepInEx 소스](https://github.com/BepInEx/BepInEx/tree/v5.4.23.2), LGPL-2.1
- [UnityDoorstop 소스](https://github.com/NeighTools/UnityDoorstop), LGPL-2.1
- [HarmonyX 소스](https://github.com/BepInEx/HarmonyX), MIT
- [MonoMod 소스](https://github.com/MonoMod/MonoMod), MIT
- [Mono.Cecil 소스](https://github.com/jbevain/cecil), MIT

해당 라이선스 원문은 Windows ZIP의 `licenses/`에 동봉합니다.
