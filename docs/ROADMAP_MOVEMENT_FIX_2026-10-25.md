# 도로 마커 구간 카운터 오류 — 0.1.5

> 이후 사용자 요청으로 v0.2에서는 이 오류를 **알려진 비치명적 이슈**로
> 명시해 발행한다. 아래의 보류 기록은 이전 의사결정이며, 오류가 해결됐다고
> 주장하지 않는다. [v0.2 배포 안내](RELEASE_v0.2.md).

## 17:34 KST 회귀 결과: 미해결

사용자의 0.1.5 플레이 후 정상 종료 로그에서 동일 계열 오류가 1회 재발했다:
`Section counter was smaller than 0. Section counter: -1 Count: 6Target point: 4`.
오류 이후 monster_truck 도착, standard_monster_truck 및 climbtruck 이벤트는
계속 진행됐으며 세션은 충돌 없이 종료됐다. 사용자는 화면상 문제를 보고하지 않았다.
브리지의 prefix 적용 로그도 존재하므로 단순히 수정 DLL이 로드되지 않은 경우는 아니다.

따라서 아래의 새 경로 초기화 누락은 코드에서 확인된 결함이지만,
그것만을 실제 로그 오류의 확정된 전체 원인으로 설명한 이전 판단은 불충분했다.
UpdateMovement의 이전 인덱스는 각 프레임 MultiLerp 전에 다시 읽히며,
MultiLerp는 경로 끝에서 -1을 기록한다. 이동 중 이후 프레임에서 -1이 다시
사용될 수 있는지는 곡선 평가값·이전 프레임·경로 재설정 호출의 계측이 더 필요하다.
현재 로그에는 이 값들이 없어 정확한 재발 순서를 단정하거나 수치 보간을 수정하지 않는다.
기존 6개 fixture 검사는 BeginPath의 인자/필드 바인딩 검사이며 이 프레임 간
상태 변화나 Unity 렌더링을 재현하지 않는다. 자동 검사 통과를 실게임 해결의
근거로 확대하지 않는다. 이 결과로 v0.2 발행을 보류했다.

## 원인

16:06 KST 로그의 `Section counter was smaller than 0. Section counter: -1
Count: 12Target point: 10`을 원본 Assembly-CSharp.dll IL과 대조했다.

1. `MathUtils.MultiLerp(List<Transform>, ..., ref pointIndex)`는 경로 끝에서
   pointIndex를 **-1**로 만든다. StopMovement(true)도 같은 값을 사용한다.
2. `RoadmapPlayerMarker.MoveAlongPath`는 새 경로·타이머·방향을 설정하지만
   **mCurrentPointIndex를 초기화하지 않은 채** UpdateMovement를 호출한다.
3. UpdateMovement는 MultiLerp 호출 전의 인덱스를 이전 구간으로 보관한다.
   새 인덱스까지 여러 구간을 처리해야 하면 이 이전 값부터 순회한다.
4. 따라서 이전 값이 -1이고 새 값이 10이면 카운터가 -1로 시작한다.
   게임은 오류를 기록하고 중간 구간의 마스크 갱신 루프를 빠져나온다.

로그의 정확한 첫 프레임 곡선/좌표 값은 저장돼 있지 않아 여러 구간을
건너뛴 기하학적 조건까지 재현한 것은 아니다. 다만 새 경로의 인덱스
초기화 누락과 -1이 오류 루프로 전달되는 코드는 직접 확인했다.

## 보완

`RoadmapMovementFix.BeginPath`를 MoveAlongPath의 Harmony prefix로 추가했다.
게임이 정상 경로로 받는 조건과 동일하게 점이 2개 이상인 경로에서만
이전 구간 인덱스를 0으로 초기화한다. 비어 있거나 짧은 경로는 원래
오류 처리를 유지한다.

MathUtils의 완료 표식 -1, 이동 곡선·속도·목적지, 일시정지/재개 메서드,
이벤트·번역·저장 데이터는 수정하지 않았다. 오류 로그 자체를 숨기는 패치가
아니라, 새 경로에서 중간 구간 순회를 정상적인 시작점에서 하도록 보완한다.
원본 게임 DLL을 변경하지 않고 브리지 **0.1.5**에서 런타임 적용한다.

## 검증

- Release x86 빌드: 경고 0 / 오류 0
- 전체 자동 검사 **43개 통과**
- 기존 게임 Mono + 보정된 MonoMod에서 실제 Harmony prefix의 인자/비공개
  필드 바인딩을 시험. 이전 인덱스 -1/0/9에서 새 경로를 시작하면 0으로
  초기화되고, null/점 1개 경로에서는 -1을 유지하며, 언패치 후 원래 값으로
  돌아오는 6개 경우 확인
- 12개 점에서 목표 구간 10까지 처리하는 경우 유효한 구간 쌍만 순회 확인
- 같은 독립 프로세스에서 후킹 해제 및 Mono 정상 종료 확인

이는 프로덕션 prefix 코드를 사용하는 테스트용 마커에 대한 검사다.
실제 Unity 도로 마스크 렌더링과 좌표 보간은 게임 실행으로 확인해야 한다.

## 로컬 적용 및 보존

0.1.5 DLL 적용 완료. 기존 종료 충돌 보정 MonoMod 해시는 동일하며
HarmonyBackend는 auto를 유지한다. 적용 전 전체 UserData·DLL·설치 기록을
`work/install/runtime_bridge_015_20261025_161144/`에 백업했다.
체크포인트 이름이 정상이라 복구 처리는 하지 않았으며, 세이브·번역 JSON·
폰트·원본 게임 파일의 해시 보존 검사를 통과했다.

다음 사용자 실행에서 확인:

1. 기존 세이브 이어하기 후 목적지로 이동. 가능하면 여러 번의 연속 이동과
   이동 일시정지/재개도 확인.
2. 마커 위치·도로 마스크가 정상이고 이동 후 이벤트가 이어지는지 확인.
3. 로그의 `Patched road marker movement: reset section index for each new valid path.` 확인.
4. Section counter 오류 재발 여부와 저장·정상 종료 확인.

게임 실행과 GitHub 릴리즈 발행은 하지 않았다.
