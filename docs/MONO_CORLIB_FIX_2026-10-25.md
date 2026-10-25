# 종료 충돌 원인 확정 및 영어 UI 복구 — 브리지 0.1.4

## 사용자 실게임 확인 완료 — 16:06 KST 세션

사용자가 직접 실행·플레이·종료 후 충돌 창이 없었다고 확인했다.
최신 Player.log(16:06:58)와 BepInEx 로그에서 다음을 재확인했다.

- 브리지 0.1.4 정상 초기화, 코드 생성 방식 auto, UI 메타텍스트 로드 성공
- Jua/GamjaFlower 두 폰트 로드 및 한국어 1,479종 글리프 검사 통과
- 이름 저장 보호와 스탯 UI 후킹 성공
- goodhost 이벤트 진행 및 체크포인트 저장 5회 기록
- 종료 가드 → GeneralManager OnApplicationQuit → Application Exit Detected →
  Memory Statistics까지 기록. Crash!!! 없음
- 새 크래시 덤프 없음. 마지막 덤프는 이전 실패 세션인 15:52:21
- 최신 체크포인트의 이름: 한글 3자, 물음표 0개

이로써 **이번 실게임 세션의 한글 로드·저장 후 이름 보존·종료 충돌 해소**를
확인했다. 모든 이벤트/장시간 플레이 검증 완료를 의미하지는 않는다.
성공 로그는 `work/testlogs/confirmed_clean_exit_20261025_160744/`에 보존했다.

별도 오류 1건: `Game.RoadmapPlayerMarker.UpdateMovement()`에서
`Section counter was smaller than 0. Section counter: -1 Count: 12Target point: 10`
발생. 발생 뒤 이동 완료·standard_shady_property 및 goodhost 이벤트 종료·
후속 저장·정상 종료가 이어졌다. 도로 마커 이동 경로의 독립 이슈로 추적하며,
현재 근거만으로 번역/종료 충돌과 연결하거나 임의 수정하지 않았다.

## 0.1.3 실행 결과

2026-10-25 15:52 KST 사용자 실행에서 BepInEx는 다음 오류로 브리지를
시작하지 못했다.

`HarmonyInteropFix.OnAssemblyLoad(...) is inaccessible from DMD<LoadFile>`

앞선 Cecil 생성기 시험이 MethodAccessException을 유발했다. 이 때문에
메타텍스트·폰트·이름 저장 보호가 모두 초기화되지 않아 UI가 영어로 보였고,
이어하기의 자동 체크포인트 저장에서 이름이 다시 `???`로 손실됐다.
그 상태에서도 최신 덤프는 이전과 동일한 Mono +0x95C48 충돌을 기록했다.
따라서 플러그인 자체의 종료 콜백만 바꾸는 접근은 충분하지 않았다.

HarmonyBackend는 **auto로 복원**했다. 기존 Cecil 후보는 실패로 판정했다.
이전 `apply_runtime_fix.py`도 이제 검증된 현재 수정 도구로 연결되므로
실패한 Cecil 설정을 다시 적용하지 않는다.

## 정확한 원인

설치된 MonoMod.Utils의 `Extensions.SetMonoCorlibInternal`은 MonoAssembly의
corlib_internal 플래그를 native 구조체의 계산된 바이트 위치에 기록한다.
이 라이브러리의 계산 결과는 이 게임의 x86 Mono에서 **+0x4F**다.

그러나 실제 `mono-2.0-bdwgc.dll`의 export
`mono_domain_assembly_foreach`를 디스어셈블하면 플래그 확인은
`cmp byte ptr [eax + 0x53], 0`이다. 즉 실제 필드는 **+0x53**에 있다.
잘못된 +0x4F는 +0x4C 포인터의 최상위 바이트에 해당한다.
거기에 true(1)를 쓰면 null 포인터가 **0x01000000**으로 변한다.
이 값은 반복된 게임 덤프의 잘못된 읽기 주소와 일치한다.

## 게임을 실행하지 않은 독립 재현

게임의 Mono DLL만 로드하는 x86 네이티브 호스트와 작은 C# 프로그램을
만들었다. Unity/Steam/원작 게임 실행 파일은 시작하지 않는다.
호스트는 테스트 Main 후 실제 mono_jit_cleanup을 호출한다.
테스트에는 게임 세이브나 이벤트를 읽고 쓰는 코드가 없다.

| 시험 | 결과 |
| --- | --- |
| 원본 Mono, 후킹 없음 | 정상 종료 |
| 원본 MonoMod, 간단한 Harmony postfix | 후킹 적용 성공 후 Mono 종료 충돌 |
| 원본 MonoMod, 종료 전 UnpatchSelf | 후킹 해제 성공 후에도 충돌 |
| 원본 SetMonoCorlibInternal만 실행 | +0x4C가 00000000 → 01000000, 실제 +0x53 플래그는 0, 종료 충돌 |
| 위치 보정 후 SetMonoCorlibInternal | +0x4C는 00000000 유지, 실제 +0x53 플래그는 1, 정상 종료 |
| 위치 보정 후 Harmony postfix | 결과 5 → 7 확인, 정상 종료 |
| 위치 보정 후 Harmony 적용·해제 | 결과 5 → 7 → 5 확인, 정상 종료 |

보정한 라이브러리에서는 auto와 Cecil 시험 모두 종료됐으나 게임 설정은
기존 정상 로드 방식인 auto를 유지한다. 새로운 로더 패키지 전체 교체나
MonoMod 22.7.31.1 시험도 별도 환경에서 진행했지만 해결되지 않아 설치하지 않았다.

원시 결과: `work/testlogs/mono_corlib_offset_fix_results.json`,
이전 대조 결과 `isolated_mono_shutdown*.json`.

## 수정 범위와 재현 조건

`build_mono_corlib_fix.ps1`는 **서드파티 로더 라이브러리의 로컬 사본**에
이 위치 보정만 추가한다. 게임 원본 Mono/Unity DLL을 수정하지 않는다.
다음 두 입력 해시와 메서드 IL 위치를 검사하며 다르면 빌드를 중단한다.

- 게임 Mono: `5C3AD7D6E2B557173D9FA4C3281136ED6992DBE25031979DFEE85D001267761C`
- 원본 MonoMod.Utils: `9D1495F147AC93C4F81F84538C1A326E8F8A6AEFC78D6289D798F3CE1162C5E9`

생성한 MonoMod.Utils SHA256:
`BBED1657D03582CDB9399339AD146E9BAFD657EFCB65EEC5364D214E40F15D8B`

다른 게임·Mono 버전·64비트·Linux에 이 오프셋을 그대로 적용하면 안 된다.
검증된 현재 Windows x86 설치본에만 적용한다.
일반 로컬 설치 스크립트에도 보정 빌드를 연결해 재설치 시 원본 라이브러리로
되돌아가 충돌이 재발하지 않도록 했다. 바이너리를 Git에 추가하지 않았다.

## 설치와 저장 데이터 보존

- 브리지 **0.1.4** 및 보정한 MonoMod.Utils를 로컬에 적용했다.
- HarmonyBackend는 **auto**다.
- 전체 UserData, 변경 전 두 DLL과 설치 기록은
  `work/install/mono_layout_fix_20261025_160101/`에 보존했다.
- 실패한 세션의 원래 설정/로그/세이브는
  `work/install/backend_recovery_20261025_155256/`에도 보존했다.
- 최신 체크포인트를 이전 파일로 되돌리지 않았다. 현재 플레이어 신원
  Player/PcProfile/Pronoun이 한글 이름을 보존한 백업과 일치함을 확인한 뒤
  Name 한 항목만 복구했다. 그 밖의 복호화된 XML은 모두 동일하다.
- 번역 JSON, 폰트, 원본 게임 DLL/번들은 변경하지 않았다. 설치 기록과
  실제 설치 파일의 해시 불일치는 0개다.
- 스탯 경계 86행 보완과 이전 이름 저장 보호도 유지한다.

## 검증 상태

- 브리지 Release x86: 경고/오류 0
- 전체 자동 검사 **42개 통과**. 독립 x86 Mono의 원본 충돌 재현과
  보정 후 포인터 보존·후킹·해제·정상 종료 검사를 포함한다.
- 이벤트 구조 독립 검사 및 기존 번역 델타 검사 통과
- 게임 실행 및 GitHub 릴리즈 발행은 하지 않음

**독립 재현에서 원인과 해결 효과를 입증했고, 후속 사용자 실게임 세션에서도
정상 종료를 확인했다.** 향후 회귀에서는 한글 메뉴와
기존 진행의 이름, 이벤트 진행 후 저장, 정상 종료를 확인한다.
BepInEx 로그에는 0.1.4와 `MonoMod method generator: auto`가 나와야 하며,
이전 MethodAccessException/브리지 로딩 실패가 없어야 한다.
