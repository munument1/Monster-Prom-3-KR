# 주인공 이름 손실 P0 및 이벤트 오류 후속 검증

조사일: 2026-10-25 (KST). 대상은 로컬 Steam Monster Roadtrip 설치본이다.
게임은 실행하지 않았고 GitHub 릴리즈를 만들지 않았다.

## 판정

확인한 체크포인트의 `???`는 **저장 단계의 문자 손실**이었다.
게임이 `XmlTextWriter`를 `new ASCIIEncoding()`으로 생성하므로
`재클린`을 `<Name>`에 기록하면 `<Name>???</Name>`이 된다.
일반 UTF-8 표시나 폰트 교체로 이미 손실된 이름을 되돌릴 수 없다.

앞서 브리지 0.1.2에 적용한 보완을 이번에 실제 게임 DLL의 암호화·복호화·
이름 읽기 함수를 호출하는 자동 검사로 추가 검증했다. 세이브 복구와
패치 설치는 앞선 작업에서 완료했고 이번 재검증에서는 세이브를 더 수정하지 않았다.

## 단계별 근거

| 경로 | 실제 설치 DLL/로컬 데이터에서 확인한 동작 | 판정 |
| --- | --- | --- |
| 이름 입력 | `PlayerCustomizeWidget.OnConfirmPlayerName`은 Trim 후 필터를 거친다. 조사된 `CorePlatformManager.ApplyProfanityFilter`는 입력을 그대로 반환한다. 과거 설정 로그에는 한글 이름이 남아 있다. | 적어도 해당 세션의 입력까지는 한글 유지 |
| 세션 저장 값 | `SessionManager.AddLocalPlayer`가 받은 문자열을 `CorePlayerData.name`에 대입 | 이 경로에 ASCII 변환 없음 |
| XML 기록 | `CoreCheckpointXmlSerializer.SerializeCorePlayerData`는 이름을 `WriteElementString("Name", name)`으로 기록. 상위 `XmlSerializer.GenerateXMLFileStream`은 ASCII XmlTextWriter 사용 | 손실 원인 직접 재현 |
| 암호화 | `CryptoUtils.EncryptXml`은 XML의 InnerXml을 `Encrypt`에 전달. Encrypt/Decrypt는 UTF-8 문자열과 Rijndael ECB/PKCS7 사용 | 암호화 이전에 발생한 물음표가 그대로 보존됨 |
| 불러오기 | `UnserializeCorePlayerData`는 `XmlSerializer.UnserializeString(XmlNode, "Name", 기존값)` 결과를 name에 대입. 해당 함수는 노드 InnerText 반환 | 저장된 값 그대로 복원 |
| 이름 변수 | `CoreEventManager.TextPatternReplacer`는 GameTag.CurrentPlayerName 분기에서 `GetPrettyPrintName`을 사용. CAPS 형식은 ToUpper 사용 | 이름 식별자와 토큰 변경 불필요 |
| 이름 색상 | `CorePlayerData.GetPrettyPrintName`은 색상 태그 + name + `[-]`를 결합 | 한글을 물음표로 바꾸는 코드 없음 |
| NGUI 텍스트 | `UILabel.set_text`는 입력 문자열을 mText에 넣고 ProcessAndRequest 호출. PlayerInfoOverlay/PlayerTurnOverlay 등은 GetPrettyPrintName 결과를 UILabel에 전달 | 저장된 `???`가 그대로 화면까지 전달될 수 있음 |
| 한글 글꼴 | 설치된 Jua/GamjaFlower의 문자 테이블에 복구한 이름의 글리프 누락 0개. 브리지는 UILabel OnEnable, LocalizedNGUIFont.Refresh, 씬 로드 시 폰트 적용 | 해당 이름의 폰트 파일 글리프는 존재. 위젯별 실제 선택 폰트/화면은 사용자 실행 확인 필요 |

특정 지도 마커의 `???`가 플레이어 이름인지 미공개 지점인지는 별개다.
원문의 의도된 물음표와 이름 치환 토큰을 일괄 수정하지 않았다.
UI 이름 8개를 영어로 되돌리는 시험도 반복하지 않았다.

## 수정과 기존 세이브 보존

- `SaveNameEncoding.WriteElementString`은 체크포인트 플레이어 직렬화의
  `Name` 값만 XML 문자 참조로 기록한다. 예를 들어 한글을 `&#x....;`로
  저장하면 ASCII 파일로도 안전하며 XML 로더가 원래 한글로 복원한다.
- `SaveNameTranspiler`는 `CoreCheckpointXmlSerializer.SerializeCorePlayerData`의
  WriteElementString 호출을 해당 도우미로 연결한다. 다른 XML 키는
  원래 WriteElementString 동작을 유지한다. 이름 하드코딩, 이벤트 토큰 변경,
  세이브 형식 변경, 원본 DLL 패치는 하지 않는다.
- 이전 작업에서 복구한 세이브는 PlayerA / pumpkin / She이며 과거 설정 로그의
  이름과 대조했다. 이름 한 항목 외 복호화 XML이 동일함을 검증했다.
- 복구 전 UserData 전체, 브리지 DLL, 설치 기록은
  `work/install/name_fix_20261025_153138/`에 보존돼 있다.
- 재검증 시 현재 체크포인트 이름은 길이 3, 한글 3자, 물음표 0개다.
  파일 SHA256은
  `2FFED404FA2702C7E6F531E063ADE8184198A8AF72300700434143A03BD5BE90`이다.
- 설치 기록과 실제 파일의 해시 불일치 0개. 원본 Assembly-CSharp.dll과
  texts_assets_all.bundle의 해시도 설치 전 기록과 일치했다.
- 기존 미커밋 번역 수정, 폰트, 세이브 백업은 유지했다.

## 자동 검증 범위

`SaveNameEncodingProbe.cs`는 원본 ASCII 기록의 손실을 재현하고 9종의 이름을
보완 코드로 왕복시킨다. `GameRuntimeContractProbe.cs`는 사용자 소유 DLL을
읽기 전용으로 로드하고 다음 **관리 코드 함수**를 실제 호출한다.

1. `CryptoUtils.Encrypt` / `Decrypt` 및 실제 `UnserializeString`: 한글·영문·
   XML 특수문자·이모지 이름 4종 보존.
2. `MultiAlwaysSucceedEventParser.CheckStat`: `+N2 STAMINA을`은 경계 조건 때문에
   실패하고, `+N2 STAMINA\u200b을`은 성공함을 재현.
3. 원본·생성 빌드·실제 설치본 각각의 evilmenu outcome 3에서 양의 Stamina와
   음의 Hype 검사 통과. 같은 파일들의 diner_doom 원시 위치 정의 3개 확인.

이 검사는 .NET 8에서 실행한다. Unity/Mono x86에서 Harmony가 실제 후킹된
상태의 전체 게임 실행·저장·렌더링을 검증한 것은 아니다. 원본 코드/게임 자산을
복사해 테스트에 포함하지 않으며, 게임이 없는 환경에서는 원본 DLL 검사를 건너뛴다.

요청한 검증 결과:

| 명령 | 결과 |
| --- | --- |
| build_playtest.py | 이벤트 27,384개 / 11개 파일 생성 통과 |
| build_ui_preview.py | 메타텍스트 2,871개 생성 통과 |
| verify_build_integrity.py | 원본 구조·번역 필드 독립 검사 통과 |
| verify_translation_delta.py | 기존 기준 및 명시적 승인 교정 검사 통과 |
| unittest discover | **38개 통과** |
| dotnet build Release --no-restore | **경고 0개 / 오류 0개** |

로컬 상세 기록: `work/testlogs/p0_regression_results.json`,
`work/testlogs/runtime_state_audit.json`. 설치 브리지 버전은 **0.1.2**다.

## 별도 이슈: evilmenu / diner_doom / 종료 충돌

과거 오류 로그에는 evilmenu outcome 3에서 `+x Stamina`를 찾지 못했다는
오류가 있다. 로컬 과거 번역 백업의 물리 인덱스 369는 실행용 토큰을
`-N2 흥`, `+N2 체력`으로 번역해 버린 상태였다. 현재 번역/설치본은
원문의 `-N2 HYPE`, `+N2 STAMINA`를 유지하며 한글 조사 앞에 U+200B 경계를
삽입한다. 실제 DLL CheckStat 함수로 현재 해당 분기의 성공을 확인했다.
기존 교정을 유지했으며 이번 조사에서 번역을 추가 변경하지 않았다.

diner_doom의 원시 이벤트는 `forbiddenjukebox`, `evilmenu`, `findbooth` 세 개다.
`RoadtripEventManager.GenerateLocationEventsDict`는 로딩된 EventFlow를 위치별로
묶고 3개인지 검사한다. 따라서 원시 정의 수와 실제 로딩 성공 수는 다르다.
과거 2/3 오류는 evilmenu 로딩 실패로 하나가 제외된 후속 오류일 가능성이 있다.
**이 인과는 추정이며 전체 파서 실행으로 확정한 것은 아니다.** 이벤트를 새로
추가하거나 위치 조건을 바꾸지 않았다.

최근 두 Player 로그(15:13, 15:15 KST)에는 해당 이벤트 로딩 오류가 없다.
그런데 두 로그 모두 OnApplicationQuit 뒤 Crash!!!가 기록돼 있다.
그러므로 이벤트 파싱 오류 해소만으로 종료 충돌까지 해결됐다고 볼 수 없다.
새 실행에서 이름/이벤트 검사와 종료 충돌 재현 여부를 각각 기록해야 한다.

## 사용자 실게임 확인 항목

1. 기존 진행 불러오기 후 플레이어 표시·대사 속 이름이 복구한 한글인지 확인.
2. 기존 진행을 저장하고 정상 종료·재실행·다시 불러오기 후 이름 유지 확인.
3. BepInEx 로그에서 버전 0.1.2 및
   `Patched checkpoint player names to preserve Unicode in ASCII XML.` 확인.
4. 새 이름 대조 시험은 **기존 UserData를 별도로 백업한 테스트 환경**에서만
   영어 `Jacqueline`과 한글 `재클린`을 각각 입력하고 저장/불러오기 비교.
   현재 진행을 초기화할 필요는 없다.
5. 이름 색상 태그, 대사 치환, 한글 글꼴, 줄바꿈과 조사 표시 확인.
6. 새 Player.log에서 evilmenu / diner_doom 오류와 종료 충돌을 따로 확인.

이 조건들의 실게임 확인 전에는 전체 해결·안정화 완료로 표기하지 않는다.
GitHub v0.2 릴리즈는 계속 보류한다.
