# Monster Prom 3 한국어화 번역 진행 기록

## 2026-10-24 번역·검증 현황

현재 대상은 **Monster Prom 3: Monster Roadtrip**입니다. 기존 게임의
영어 슬롯을 변경하지 않고 텍스트·UI 번역을 별도 JSON으로 유지합니다.

| 범주 | 번역 완료 | 원문 후보 | 진행률 |
| --- | ---: | ---: | ---: |
| 이벤트 대사·선택지·행동 | 1,936 | 27,384 | 7.07% |
| UI·메타텍스트 | 445 | 2,871 | 15.50% |
| **합계** | **2,381** | **30,255** | **7.87%** |

이전 GitHub `main` 커밋 `9d5d449`의 1,081개에서 **이번 작업으로 1,300개**를
추가했습니다. `english_events_standard` 259개, `english_events_tutorial`
206개, `english_events_gameover` 250개는 각 파일의 **현재 추출된 번역 후보 전체**를
채웠습니다. 이에 비해 maingame·pitstop·endings·bubbles 등은 대량의
미번역 텍스트가 남아 있습니다.

### 현재 에셋별 번역 건수

| asset | 번역 수 |
| --- | ---: |
| `english_events_maingame` | 246 |
| `english_events_pitstop` | 325 |
| `english_events_endings` | 315 |
| `english_events_bubbles` | 270 |
| `english_events_standard` | 259 |
| `english_events_gameover` | 250 |
| `english_events_tutorial` | 206 |
| `english_events_prologue` | 26 |
| `english_events_gachashop` | 30 |
| `english_events_epilogue` | 8 |
| `english_events_default` | 1 |
| `english_metatexts` | 445 |

### 검증 방법 및 실게임 적용과의 차이

```powershell
python -X utf8 scripts\build_playtest.py
python -X utf8 scripts\verify_build_integrity.py
python -X utf8 scripts\build_ui_preview.py
python -X utf8 scripts\audit_progress.py
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts\prepare_camp_fonts.py --audit-only
```

- 번역 JSON은 **원본 TextAsset SHA-256**, 텍스트의 물리 line,
  이벤트명, 영어 텍스트 SHA-256을 보존하며, 원문에 없는 변수·태그·숫자·분기를
  새로 만들지 않습니다.
- 독립 `verify_build_integrity.py` 검사는 **번역한 행의 네 번째 필드 외에는
  11개 이벤트 TXT의 모든 행이 원본과 정확히 일치**해야 통과합니다.
- 3편에 설치된 기존 한국어 테스트 패치는 이전 시점의 이벤트 TXT를 사용합니다.
  이번 번역 JSON·로컬 빌드 결과를 **실게임에 다시 설치하지 않았고**,
  대사·선택지 표시·저장/불러오기 회귀 검증은 아직 진행해야 합니다.
- 2편의 Jua/감자꽃 글꼴은 한국어 고유 음절 1,057종 모두를 포함하지만,
  모든 특수문자가 지원되는 것은 아닙니다. 신규 UI·대사 실게임 화면 검증 필요.
- `work/`, `build/` 아래 원본/폰트/게임 리소스는 Git에서 제외하며,
  **비공개 GitHub 저장소에도 이 바이너리들을 업로드하지 않습니다.**

다음 작업은 본편·휴게소·엔딩·버블의 남은 번역과 선택지·행동 문구 보강,
전역 용어·말투 통일, 실게임 폰트/줄바꿈 회귀 검증입니다.

독립 표본 언어 검수에서 현재 구조 오류나 중대한 오역은 추가로 확정되지
않았습니다. 다만 **Joy / Zoe 모두 `조이`로 표기되는 동명이인 위험**이 확인돼
`TRANSLATION_GUIDE.md`에 별도 주의를 기록했습니다. 두 캐릭터의 고유명사를
임의로 일괄 변경하지 않고 시리즈 맥락을 확인하도록 관리합니다.
