# 개발자 보고서 — 서브플롯 실측 → AEG → 장기플래너 갭 → 학습 커리큘럼 (2026-06-26)

수신: 개발자(집·GPU 트랙) / 발신: 계획·설계 모드(무GPU) / 허브 HEAD 기준: 982e3c3
관련 산출(이미 push): `docs/measurement/SUBPLOT-RATIO-MEASUREMENT-v1.md`, `examples/measure_subplot_ratio.py`, `docs/design/DESIGN-AFFILIATION-ENSEMBLE-v1.md`, `docs/design/DESIGN-PLANNER-LEARNING-CURRICULUM-v1-DRAFT.md`, `docs/sessions/2026-06-26_subplot_and_planner_curriculum_session.md`
동봉 명세서: `docs/design/SPEC-PLC-A1-SUBPLOT-ALLOCATOR-v1.md`(다음 단계 구현 명세)

---

## 0. 한 줄 보고
실측으로 "드라마 서브플롯 ≈48%"를 상수로 확정했고, 그 층이 현재 생성 파이프라인에 **구조적으로 누락**됨을 코드로 확인했으며(EpisodePlan에 서브플롯/소속/역할 필드 없음), 이를 메우는 **학습 커리큘럼(PLC)**의 첫 구현 단위를 명세로 제출한다.

---

## 1. 무엇을 실측했나 (검증된 사실)

| 지표 | 드라마(122편/2,264회) | 영화(82편) |
|---|---|---|
| 주변 인물 대사 점유율 top-4 | 평균 0.477 / 중앙값 0.459 | 평균 0.321 / 중앙값 0.318 |
| 주변 인물 대사 점유율 top-2 | 평균 0.628 | — |
| 회차 ≥40% 비율 (top-4 / top-2) | 72% / 96% | 23% / 78% |
| 순수 서브플롯 씬(주연 0명) | 평균 0.239 | — |

- 방법: 화자 필드 없는 코퍼스 → 행머리 한글 이름 토큰 추출 → 작품별 빈도순위로 주연/주변 분리 → 조사결합(영달이/영달과→영달) 병합. GPU 0, 결정론적, 재현 가능(`measure_subplot_ratio.py`).
- 결론: **40%+ 서브플롯은 드라마 고유 구조 상수**(영화는 32%로 유의 낮음). 사용자(작가) 직감의 정량 확증.
- 정직한 한계: 화자 토큰 기반이라 직장군/가족군 구분, 메인-서브 교차 시점은 미라벨(→ v2).

## 2. 무엇이 증명됐고 무엇이 안 됐나 (플래너 현주소)

증명됨:
- 배선 PoC — 12기관 위상정렬로 16/24부작 자율 산정. K궤적 `[4,3,4,4,4,4,5,6,6,6,5,5,5,4,4,4]`(중반 아크형), 갈등압력 0.057→0.405, 24부작 무수정, 5 tests, 결정적.
- FrontierPort(gpt-4o-mini 프록시)로 실 한국어 대본 산문을 파이프에 흘림 — "수도관에 물 흐름" 실증.

미증명(정직한 경계):
- **문학 품질·작가팀 수준 = 비주장·미측정**(템플릿/프록시 기준). LLM1Port(집 4070 졸업 8B) 실측 미실행.
- **플래너는 100% 공식 산정**. `EpisodePlanner._compute_k(...)`가 K를 공식으로 계산. 학습 0.

## 3. ★코드로 확인한 핵심 갭 (이번 보고의 골자)

`literary_system/episode/episode_planner.py`의 `EpisodePlan` 데이터클래스 필드:
`microplot_count(K) · total_scene_budget · act_position · reveal_budget_per_slot · emotional_targets · conflict_weights · slot_functions · planning_trace`

→ **서브플롯 배분·소속군·role_type(3종) 필드가 아예 없다.** 즉 실측한 48% 서브플롯 층을 표현할 자리 자체가 플랜 스키마에 없다. `episode_loop()`도 인물 4명(chars[0..3])만 고정 사용. AEG 설계가 지목한 빈칸이 코드로 재확인됨.

귀결: 두 종류의 학습은 직교한다 —
- 판단 학습(loop-C/per-token DPO/5축 Critic): **있음**.
- 생성 플래너 학습(구조·서브플롯 배분): **없음**. ← 본 보고가 메우려는 대상.

## 4. 제출하는 명세 (다음 단계, §별도 문서)
PLC(플래너 학습 커리큘럼) 초안의 **첫 구현 단위 = A1: Subplot Allocator BC**.
- 가장 좁고·완전히 라벨된·즉시 빌드 가능한 단위만 명세화(K/tension 학습은 후속 마일스톤).
- 기존 공식 플래너는 floor로 보존, 그 위에 "서브플롯 배분 층"만 학습으로 얹음(설계철학 정합).
- 라벨러 = 오늘 측정 스크립트가 씨앗. DoD = 생성 16부작을 같은 스크립트로 재측정 0.46±0.10.
- 상세: `docs/design/SPEC-PLC-A1-SUBPLOT-ALLOCATOR-v1.md`.

## 5. 개발자 의사결정 요청 사항
1. 플랜 표상: `EpisodePlan`에 `subplot_allocation` 필드 추가(스키마 확장) 승인 여부.
2. 학습 좌석: 신규 `PlannerPort`(SubplotAllocator seam) 도입 vs 기존 GenerativePort 확장 — 명세는 신규 좌석 권장.
3. A1 BC 데이터 규모: 122편 전수 vs Tier-1 우선. 명세 기본값 = 전수(held ≥250회차).
4. 실 학습 환경: 집 4070(졸업 8B+lora) 위에 BC 헤드 vs 별도 경량 분류기 — 명세는 후자(경량) 우선 권장(저비용 첫 관문).

## 6. 자기점검(보고의 약점)
- A1은 "서브플롯 배분"만 학습, K·교차·payoff는 여전히 공식 → 부분 학습이지 전면 플래너 학습 아님(의도된 단계화).
- 라벨러가 화자 토큰 기반이라 소속군 유형 라벨은 v2 의존.
- DoD 임계 0.46±0.10은 AEG 계승 잠정값(졸업 계약 아님).
