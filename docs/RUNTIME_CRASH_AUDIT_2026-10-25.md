# 종료 충돌과 플레이 중 오류 조사 — 2026-10-25

## 확인된 사실

최근 Player.log(15:40 KST)는 브리지 0.1.2로 기존 게임을 이어서 진행한
94초 세션이다. tutorial_resources1, standard_gas_trolls, payforgas가 끝났고
체크포인트 저장이 두 차례 기록됐다. 크래시 전에 `>ERROR`, `[Error`,
`Exception:`으로 기록된 오류는 0건이었다. 이 표본만으로 모든 분기의
플레이 안정성을 보장할 수는 없다.

종료 시 GeneralManager.OnApplicationQuit → Application Exit Detected →
통계 기록 뒤 Crash!!!가 발생했다. 미니덤프 예외 컨텍스트와 x86 프레임을
읽은 결과 최초 오류는 **mono-2.0-bdwgc.dll + 0x95C48**의 읽기 접근 위반
`0xC0000005`이며 대상 주소는 `0x01000000`이다.
프레임은 mono_domain_free → Mono 내부 해제 → mono_jit_cleanup → UnityPlayer다.
로그 뒤쪽에 출력된 UnityPlayer/Windows 창 처리 스택만으로 충돌 원인을
판정하면 실제 최초 예외 지점을 놓치게 된다.

로컬 덤프 13개 중 12개가 같은 Mono 오프셋과 접근 주소를 갖고,
한 개는 ntdll에서 읽기 접근 위반을 보고한다. Mono 코드에서 실제 메모리
오염을 처음 일으킨 주체까지는 덤프만으로 확정하지 못했다.
Unity의 Mono 소스에서도 mono_domain_free는 종료 시 도메인 자원을 해제하는
함수다. [Unity Mono domain.c](https://github.com/Unity-Technologies/mono/blob/unity-2021.3-mbe/mono/metadata/domain.c)

## 추가 발견 및 수정: 스탯 토큰 86행 누락

게임 DLL의 RegexUtils.GetRegexStat을 직접 호출해 원문과 게임용 번역의
**실제 인식되는** 스탯 표현을 비교했다. 기존 보완은 `+N2 MAGIC을` 형식에만
U+200B 경계를 넣었다. `-2 STAMINA를`, `+1 MAGIC을` 등 N이 없는 직접 수치는
한글 조사와 붙어 있으면 원본 게임 정규식이 인식하지 못했다.

생성기의 경계 보완을 N 유무와 관계없이 적용하도록 확장했다.
번역 JSON과 문장은 보존했고, 생성된 본편 TXT의 **86행에 경계 문자 92개**만
추가됐다. 새 파일에서 U+200B를 제거한 결과와 이전 설치본에서 U+200B를
제거한 결과가 정확히 동일함을 적용 전에 검사했다.

수정 후 실제 설치된 11개 이벤트 파일 검사 결과:

- 네 번째 필드를 가진 원문 행 28,036개 검사
- 스탯을 가진 원문 행 1,061개 / 스탯 표현 1,342개
- 원문과 설치본의 게임 정규식 인식 결과 **불일치 0개**

이는 스탯 표현 인식 검사이며 전체 이벤트 엔진의 분기·조건·플레이 실행
검사를 대체하지 않는다. evilmenu 분기의 기존 교정과 이름 보존도 유지했다.

## 종료 충돌 대응 후보 0.1.3

1. OnApplicationQuit 이후 메타텍스트 교체와 UI·폰트 적용 콜백이 종료
   중인 Unity 객체를 다루지 않도록 가드를 보강하고 씬 콜백을 해제했다.
   기존 종료 중 폰트 해제/Harmony 언패치 회피도 유지한다.
2. BepInEx의 HarmonyBackend를 `auto`에서 `cecil`로 변경했다.
   설치된 Preloader가 이 설정을 MONOMOD_DMD_TYPE에 전달하고 MonoMod가
   Cecil 생성기로 분기하는 것을 로컬 DLL IL에서 확인했다.
3. 다음 실행 로그에 선택된 코드 생성 방식과 종료 가드 진입 기록을 남긴다.

Cecil은 Reflection.Emit 문제에 대한 공식 대체 설정이다.
[BepInEx troubleshooting](https://github.com/BepInEx/bepinex-docs/blob/master/articles/user_guide/troubleshooting.md)
다만 그 안내는 이번 Mono 종료 충돌의 원인/해결을 입증하지 않는다.
**생성 방식 호환성은 가설이며, 변경 후 종료 충돌 해소는 미검증**이다.
종료를 강제 중단하거나 크래시 창만 숨기는 처리는 추가하지 않았다.

## 보존 및 적용 내역

수정 DLL, 새 본편 TXT, BepInEx 설정을 로컬에 적용했다.
버전은 0.1.3이며 이름·로딩·스탯 UI 보완을 포함한다.

백업: `work/install/runtime_fix_20261025_154900/`

여기에 적용 직전 UserData 전체, 기존 DLL·이벤트 TXT·BepInEx.cfg,
설치 기록과 최근 로그를 보존했다. 적용 과정에서 원본 DLL/텍스트 번들,
현재 세이브, 번역 JSON, TTF/폰트 번들의 해시가 모두 유지됨을 확인했다.
파일별 새 해시와 보호 파일 목록은 같은 폴더의 update.json에 있다.

원복 시에는 이 작업에서 바꾼 DLL·이벤트 TXT·BepInEx.cfg·설치 기록만
검증 후 되돌린다. **UserData 백업을 자동 복원하지 않는다**.
이후 플레이한 진행 데이터를 이전 백업으로 덮어쓰면 안 된다.

코드/도구:

- scripts/build_playtest.py: N 없는 스탯 토큰 경계 보완
- src/RoadtripKoreanFontBridge/RoadtripKoreanFontBridgePlugin.cs: 종료 가드/진단 로그
- tests/AllEventStatProbe.cs: 실제 게임 DLL 정규식으로 전체 스탯 표현 비교
- scripts/audit_runtime_crashes.py: 게임 실행 없이 로그/덤프 요약 재생성
- scripts/apply_runtime_fix.py: 해시 검사, 백업, 후보 적용. 반복 적용용이 아니며
  현재 backend가 auto가 아니면 적용을 중단한다.

## 검증과 다음 실행

- Release x86 빌드: 경고 0 / 오류 0
- 자동 검사 **40개 통과**, 이름 왕복·실제 DLL 검사 포함
- 전체 이벤트 구조 및 번역 델타 검사 통과
- 실제 설치본의 전체 스탯 표현 인식 검사 통과
- 게임 실행 및 GitHub 릴리즈 발행은 하지 않음

사용자 다음 실행에서 확인할 항목:

1. 로그의 브리지 0.1.3, `MonoMod method generator: cecil` 확인.
2. 기존 세이브 이어하기에서 이름·글꼴·대사·선택지 확인.
3. 이벤트를 진행하고 자원 수치 변화 및 자동 저장 확인.
4. 메뉴로 돌아간 뒤 정상 종료. 크래시 창/새 Crash 폴더 생성 여부 확인.
5. `Quit requested; Korean UI/font callbacks are disabled for runtime teardown.`
   로그 확인. 그 뒤에도 크래시가 있으면 새 덤프의 예외 위치를 비교한다.

계속 충돌한다면 Cecil 변경의 효과를 판정한 뒤 로더/후킹 경로를 분리해야 한다.
브리지나 로더 비활성화 시험은 한글 세이브를 ASCII로 다시 저장할 위험이 있으므로
현재 진행 대신 세이브·설정·로그가 분리된 테스트 복제본에서 수행해야 한다.
사용자가 직접 실행 테스트하기로 한 상태를 유지한다.
