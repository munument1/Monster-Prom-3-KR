# Monster Roadtrip 한국어 패치 v0.2

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

## 다운로드와 설치

**Windows 일반 사용자는 `Monster-Roadtrip-KR-v0.2-Windows-DragDrop.zip`을 선택하세요.**
검증 대상은 Steam build 25955894, Unity 2021.3.15f1, Windows x86입니다.

1. 게임을 종료하고 ZIP을 별도 폴더에 풉니다.
2. 게임 설치 폴더를 대상으로 아래 읽기 전용 검사를 먼저 실행합니다.

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\VERIFY-WINDOWS.ps1 -GamePath "C:\Games\Steam\steamapps\common\Monster Prom 3 - Monster Roadtrip"
   ```

   PASS가 아니면 설치하지 마세요. Steam의 로컬 파일 탐색으로 자신의 경로를 찾을 수 있습니다.
3. 기존에 같은 이름의 파일이 있으면 먼저 백업합니다. 기존 BepInEx 모드가 있다면
   코어 라이브러리 교체가 다른 모드에 영향을 줄 수 있으므로 충돌 여부를 확인하세요.
4. `BepInEx`, `MonsterRoadtrip_Data`, `winhttp.dll`, `doorstop_config.ini`,
   `.doorstop_version`을 게임 설치 폴더에 복사합니다. 갱신 설치 시에는 패키지에 들어 있는
   **MonoMod.Utils.dll과 브리지 DLL도 함께 갱신**해야 종료 충돌 수정이 적용됩니다.
5. 기존 `BepInEx/config/BepInEx.cfg`가 있으면 `[Preloader]`의
   `HarmonyBackend = auto`인지 확인합니다. 실패했던 `cecil` 설정은 사용하지 않습니다.
6. 게임 언어를 **English**로 선택해 실행합니다. 한국어 텍스트가 영어 슬롯을 대체합니다.

Windows ZIP에는 한국어 UI·이벤트·브리지·보정된 x86 로더를 포함합니다.
**주아·감자꽃 파일/게임에서 재구성한 폰트 번들은 배포하지 않습니다.**
기존 로컬 주아·감자꽃 번들이 있다면 그대로 보존해 사용하며, 없는 PC에서는 Windows의
맑은 고딕을 대체 글꼴로 시도합니다. 맑은 고딕 대체 경로는 이전 로컬 실행에서
성공했지만 이번 0.1.5 플레이 검증은 주아·감자꽃 환경에서 진행했습니다.

`Monster-Roadtrip-KR-v0.2-manual-overwrite.zip`은 **이벤트 TXT 11개만** 담은
수동 설치 보조 파일입니다. UI·폰트·이름 저장·종료 충돌 수정은 포함하지 않습니다.
Linux/Steam Deck 구동은 검증하지 않았고 Windows 로더를 Linux에 설치하면 안 됩니다.
`Monster-Roadtrip-KR-100pct-source-testkit.zip`은 번역 JSON·소스·재현 스크립트 키트입니다.

제거 시 패키지의 파일 목록을 기준으로 추가한 파일만 지우고, 원래 있던 파일은 백업에서
복원하세요. `UserData` 및 게임 원본 DLL/번들은 삭제·덮어쓰기 대상이 아닙니다.

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
