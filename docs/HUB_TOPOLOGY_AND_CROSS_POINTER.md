# 허브 이원화 사고와 교차 포인터 (2026-08-15)

## 사고
회사 세션이 확증 트랙(CT) 실험 문서를 "허브에서 찾을 수 없다"고 보고. 조사 결과 **소실이 아니라 저장소 분리**였다.

| 저장소 | 범위 | 주 사용 세션 |
|---|---|---|
| `limsanghyuk/literary-os` (**본 저장소**) | 엔진 v795/v14 · **확증 실험 CT-01~CT-10** · 채점 규약 v2 · 거시기획 설계 · 세션 인계 | 집(Claude) |
| `limsanghyuk/v1700-literary-os` | 드라마 분석 Stage01–04 · THICK · PlannerInput/Runtime · EXT6 · 작품 클레임 | 회사·GPT 트랙 |

GPT 마스터 핸드오프(`00_START_HERE.md`)가 라이브 허브로 **v1700만** 지목하고 있어, 그 문서로 부팅한 세션은 CT 문서를 볼 수 없었다. 본 저장소의 커밋은 전량 정상(2026-08-04~08-14, 소실 0건 확인).

## 조치
1. v1700에 미러 브랜치 푸시: **`claude-confirmatory-track-bridge`** — `experiments/confirmatory_track/`(CT 문서 45건 + 요약 README + `CROSS_HUB_POINTER.json`). v1700은 main 직접 푸시가 금지(PR 필수)되어 **PR 병합이 필요**하다: https://github.com/limsanghyuk/v1700-literary-os/pull/new/claude-confirmatory-track-bridge
2. 본 문서를 양 허브의 교차 포인터로 사용. 미러는 **읽기용 사본**이며 판정·수치의 정본은 본 저장소다.

## 신규 세션 규칙 (양쪽 공통)
- 데이터(작품·THICK·Runtime) 질문 → v1700.
- 실험·판정·채점 규약·엔진 질문 → literary-os `docs/tracks/confirmatory/` · `docs/standards/` · `docs/sessions/`.
- 어느 쪽으로 부팅했든 **상대 허브를 반드시 함께 조회**할 것. 한쪽만 보면 오늘과 같은 "결과 없음" 오판이 재발한다.
