# Track1 밀도 보강 — W1 핸드오프 (회사→집)

**작성일**: 2026-07-22 (회사 PC 세션 종료 인계)
**작성자 역할**: Opus = 설계·게이트·팬인 / 실저작 = Sonnet 병렬
**목적**: 오늘 회사 PC에서 완료한 W1(6작) 밀도 보강 결과와 잔여 스코프를 집 PC에서 즉시 이어받도록 정리.

---

## 0. 한 줄 요약
W1 6작(궁·카인과아벨·여우야뭐하니·마왕·스카이캐슬·하얀거탑) 그래프층 밀도 보강 **완료·게이트 PASS**. 보강 arc 파일 240개(chararc 120 + relarc 120)를 허브에 동봉. 집 PC는 W2부터 이어서 진행.

## 1. 트랙 정리 (측정 결과)
- **Track2(잔여 오류 트랙)는 측정으로 드롭 판단** — 본 인계 범위 아님. 잔여오류(참고): SCENE_PROSE_SHORT 106, EXACT_DUPLICATION 80, LOCAL_NONFORWARD 23, MASKED_REPETITION_THRESHOLD 52. 밀도 보강과 별개 트랙.
- **Track1(밀도 보강)만 진행** — char-arc/ep 중앙값 ≥5 AND rel-arc/ep 중앙값 ≥4 (GRAPH_DENSITY_FLOOR) 충족이 목표.

## 2. W1 결과 (실측)

| 작품 | eps | char총계(추가) | rel총계(추가) | char/ep중앙 | rel/ep중앙 | 게이트 오류수(=baseline) |
|---|---|---|---|---|---|---|
| 궁 | 24 | 120 (+72) | 96 (+48) | 5.0 | 4.0 | 4 |
| 카인과아벨 | 20 | 100 (+60) | 80 (+40) | 5.0 | 4.0 | 1 |
| 여우야뭐하니 | 16 | 80 (+48) | 67 (+35) | 5.0 | 4.0 | 0 |
| 마왕 | 20 | 101 (+61) | 82 (+42) | 5.0 | 4.0 | 1 |
| 스카이캐슬 | 20 | 121 (+81) | 102 (+62) | 6.0 | 5.0 | 1 |
| 하얀거탑 | 20 | 140 (+100) | 100 (+60) | 7.0 | 5.0 | 0 |

**핵심 검증**: 오류수가 보강 전 baseline과 **정확히 일치**(신규 EXACT_DUPLICATION/MASKED/grounding 오류 0). → 번호 패딩이 아니라 실제 원본 씬 근거 보강임을 입증. below_floor 전 작품 공란.

## 3. 프로벤넌스(by 태그) 메모
- 추가행은 모두 sonnet 계열 태그(`sonnet_reading` 및 `sonnet-4.6 / density-reinforcement 2026-07-22` 2가지 포맷 변형). **정상** — 초기 세션에서 공백 포함 정규식만 매칭해 4작 0건으로 오탐했으나 재검 결과 전작 추가행이 sonnet 태그 보유. 정규화 불필요(코스메틱 변형만).

## 4. 게이트 명령 (집 PC에서 그대로)
```
cd <ROOT>/db/seqcard_ko/seqcard_ko && \
python3 tools/current/validate_semantic_quality_v2.py \
  --root <ROOT>/db/seqcard_ko --work <작품명>
```
`--root` = OUTER(=seqcard_ko 폴더를 담고 있는 상위). JSON의 `density` 블록에 char_arc_per_ep_median / rel_arc_per_ep_median / below_floor / status.

## 5. 트리 구조 차이 (중요)
- **로컬 = 2중 트리**: `db/seqcard_ko/seqcard_ko/authored_chararc/...`
- **허브 = 플랫 트리**: `seqcard_ko/authored_chararc/...` (중첩 inner 없음)
- 인계 파일은 허브 플랫 규격에 맞춰 `seqcard_ko/authored_chararc|authored_relarc/`에 직접 배치함.

## 6. 잔여 스코프 (집 PC에서 이어서)
- **W2 (10작)**: 대장금(54ep — 단독 권장), 국희, 라이벌, 마지막전쟁, 비밀, 킬미힐미, 토마토, 뉴하트, 더킹투하츠, 밀회
- **W3 (8작)**: 대물, 신화, 우아한가, 파리의연인, 피아노, 경성스캔들, 미안하다사랑한다, 성균관스캔들
- **W4 (1작)**: 최강칠우 (from-scratch)
- **절차**: 작품별 Sonnet 병렬 에이전트에 자기완결 프롬프트 → 원본 씬 근거로 chararc/relarc APPEND(덮어쓰기 금지) → 2단 게이트(개별→팬인)로 below_floor 공란 & 오류수=baseline 확인.
- **주의(안티게이밍)**: 신규행은 DISTINCT 실제 씬 참조 + UNIQUE delta/evidence. 인물명은 trigger 씬에 실제 등장(그라운딩).

## 7. 동봉 파일
- `arc_files/` 하위에 W1 6작 chararc 120 + relarc 120 (tar도 포함: `w1_arc_files.tar.gz`).
- 허브 `seqcard_ko/authored_chararc|authored_relarc/`에도 동일 파일 커밋됨(집에서 pull만 하면 됨).

## 8. 브리프 원본
설계 브리프 전문: `C:\claude\TRACK1_reinforcement_brief_v1.md` (deficit 표·스키마·안티게이밍 §3·2단게이트 §4·W1~W4 배칭 §5·잔여오류 §6·self-audit §7).
