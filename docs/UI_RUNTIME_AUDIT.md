# 2026-10-25 UI 누락 및 종료 오류 조사

## 저장 후 주인공 이름 `???` — 브리지 0.1.2

- 체크포인트를 읽기 전용으로 복호화한 결과, `CorePlayerData/Name` 자체가
  `???`였다. 이 세이브의 문제는 글리프 표시가 아니라 저장된 문자열 손실이다.
- 원본 `BeautifulGlitch.XmlSerializer.GenerateXMLFileStream`은
  `new ASCIIEncoding()`으로 `XmlTextWriter`를 생성한다.
  원본과 같은 XML 기록 방식에서 `재클린`이 `???`로 바뀌는 것을 재현했다.
- `CoreCheckpointXmlSerializer.SerializeCorePlayerData`의 XML 문자열 쓰기만
  후킹했다. `Name` 항목의 비ASCII 문자를 XML 문자 참조로 기록하고,
  다른 항목은 원래 `WriteElementString`을 호출한다. 기존 ASCII 로더와
  암호화 형식을 유지하며 이름의 한글·보조 평면 문자도 보존한다.
- 실제 C# 보완 코드를 사용한 회귀 검사에서 원본 손실 재현 및 한글,
  공백, XML 특수문자, 영문, 이모지 등을 포함한 9개 이름의 왕복을 검증했다.
  전체 자동 검사 **37개 통과**, Release/x86 빌드 경고·오류 0개.
- 기존 체크포인트에는 PlayerA / pumpkin / She 플레이어 한 명만 있었다.
  과거 크래시 로그의 동일한 플레이어 설정에 `Name:재클린`이 기록돼 있어
  그 이름으로 복구했다. 복호화된 XML은 **이름 한 항목 외 모두 동일**함을
  비교했으며, 재암호화 결과의 재복호화도 검증했다.
- DLL·설치 기록 및 **UserData 전체 백업**:
  `work/install/name_fix_20261025_153138/`. 설치한 브리지는 **0.1.2**다.
- 게임은 실행하지 않았다. 사용자는 기존 진행을 불러와 이름을 확인하고,
  저장·종료·재실행·다시 불러오기를 거친 뒤에도 한글이 유지되는지 확인한다.
  0.1.2는 기존 로딩·스탯 UI 보완을 포함하며 종료 충돌의 해결 여부는 미확인이다.

## 확인한 원인과 보완

- 첫 시작 화면: `level0`의 `LoadingLabel`(MonoBehaviour path ID 31)에
  `LOADING`이 직접 저장돼 있다. 일반 로딩 화면 `level2`의 `LoadingText`
  (path ID 45)에도 `LOADING...`이 저장돼 있다. 브리지 0.1.1은
  `SplashScreen/LoadingLabel`, `Loading/LoadingText`의 해당 원문만
  `불러오는 중...`으로 치환한다.
- 우측 상단 스탯: 원본 `Game.StatWidget.Initialize`의 두 오버로드가
  `StatType.ToString()` 결과를 `nameLabel.text`에 직접 넣는다.
  번역 JSON의 `STA_*` 값은 작성돼 있지만 이 코드에서 사용하지 않는다.
  브리지 0.1.1은 두 메서드의 UILabel 문자열 대입 직전에 게임의
  `CoreTextManager.GetText("STA_" + 이름.ToUpperInvariant(), true)`로 표시 문자열을
  변환한다. 애니메이션용 보조 라벨을 복제하기 전에 적용한다.
  내부 열거형, 이벤트 파서와 저장 데이터의 스탯 식별자는 변경하지 않는다.
- 한글 폰트 적용과 UI 문자열 치환은 별개다. 이 두 누락의 직접 원인은
  TextMeshPro 지원 여부가 아니라 메타텍스트를 거치지 않는 표시 경로다.

## 실행 오류의 현재 증거

조사 시 보존한 `Player.log`, `Player-prev.log`에는 메인 게임 진입 후
`GeneralManager OnApplicationQuit` / `Application Exit Detected`가 기록되고,
그 뒤 `Crash!!!` 및 UnityPlayer 네이티브 스택이 나온다.
현재 확인된 충돌 시점은 **종료 처리 중**이다. 해당 로그에는 종료 전
관리 코드 예외가 확인되지 않았다. 번역, 글꼴, 로더, 오버레이 중 어느 것이
원인인지는 이 증거만으로 확정할 수 없다. 0.1.1은 이 충돌의 해결을 보장하지 않는다.

## 정적 검증과 사용자 실행 테스트

- 브리지 Release/x86 빌드: 경고 0, 오류 0.
- Python 자동 검사: 36개 통과.
- 이벤트 구조 독립 검사: 11개 파일, 번역 필드 27,384개 통과.
- 사용자가 직접 실행 테스트하기로 했으므로 에이전트는 게임을 실행하지 않았다.
- 기존 브리지 DLL, 설치 기록, 게임 로그는 교체 전 `work/install/ui_fix_*/`에
  백업한다. DLL 교체 뒤 설치 기록의 해당 DLL 해시만 갱신한다.

게임 언어를 영어로 유지한 상태에서 확인할 항목:

1. 처음 시작 및 화면 전환 때 로딩 문구가 `불러오는 중...`으로 표시되는지.
2. 게임 우측 상단이 `흥 / 마력 / 정신 / 돈 / 영혼 / 체력`으로 표시되는지.
3. 스탯창의 펼침·접힘과 숫자 변화 때 영문 이름이 다시 나타나거나 잘리지 않는지.
4. 정상 종료 때 오류 창이나 충돌이 다시 발생하는지.

실행 후에는 `BepInEx/LogOutput.log`에서 브리지 버전 `0.1.1`과 두
`Patched stat names` 기록을 확인할 수 있다. 종료 오류가 재현되면
`Player.log`와 최신 크래시 기록을 기준으로 별도 원인 분리 테스트가 필요하다.
