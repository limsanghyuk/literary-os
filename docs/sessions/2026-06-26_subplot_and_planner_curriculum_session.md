# 세션 정리 — 서브플롯 실측 → AEG → 장기플래너 실측/학습 갭 → 커리큘럼 초안 (2026-06-26)

작성: 계획·설계 모드(무GPU). 성격: 누적 발판 문서. 트랙: 메인(LLM-0→3).

## 0. 오늘의 흐름 한눈에
실측(드라마 서브플롯 48%) → 설계(AEG) → 정직한 진단(장기플래너는 어느 선까지 형성됐나) → 갭 발견(플래너 학습 백지) → 초안(PLC 커리큘럼). 네 산출물이 하나의 사슬로 누적됐다.

## 1. 서브플롯 비율 실측 (검증된 상수)
- 범위: 드라마 122편(2,264회차) + 영화 82편, 화자 발화 94만여 행. GPU 0, 결정론적.
- 방법: 화자 필드 없는 코퍼스에서 행머리 이름 토큰 추출 → 빈도순위로 주연/주변 분리 → 조사결합(영달이/영달과→영달) 병합으로 인공분할 제거.
- 결과: **드라마 주변 인물 대사 = 회차당 평균 47.7% / 중앙값 45.9%(top-4)**, top-2 기준 62.8%. 회차의 72%(top-4)·96%(top-2)가 40% 이상. 순수 서브플롯 씬(주연 0명) 평균 23.9%.
- **드라마 고유성**: 영화 top-4 평균 32.1%로 뚜렷이 낮음 → 회차 호흡으로 직장·가족 병렬 전개하는 드라마 구조 상수.
- 산출: `examples/measure_subplot_ratio.py`, `docs/measurement/SUBPLOT-RATIO-MEASUREMENT-v1.md`, `subplot_ratio_results.json`.

## 2. Affiliation Ensemble Generator (AEG) 설계
- 문제: 현 `wiring_poc`는 인물 4명 하드코딩 → 위 40~50% 서브플롯 층 누락.
- 해법: 소속 그래프(직장군+가족군) 1급 스키마화, role_type 2종→3종(주인공/반대주인공/주변), 씬 예산 40~50% 서브플롯 스케줄러, causal_plot_graph 교차+수정전파 훅.
- DoD: 생성 16회차를 measure 스크립트로 재측정해 중앙값 0.46±0.10. 산출: `docs/design/DESIGN-AFFILIATION-ENSEMBLE-v1.md`.

## 3. 장기 플래너 — "어느 선까지" 정직한 재확인
- 명시했던 선: **구조 골격 자율화는 증명**(배선 PoC — 12기관 위상정렬로 16/24부작 자율 산정, K궤적 아크형 `[4,3,4,4,4,4,5,6,6,6,5,5,5,4,4,4]`, 갈등압력 0.057→0.405, 24부작 무수정, 5 tests). FrontierPort로 실 한국어 산문까지 흘림(프록시).
- **명시 안 한 선**: 문학 품질·"작가팀처럼 좋게 쓴다"는 비주장·미측정(템플릿/프록시 기준).
- 실측 실태: 플래너가 "구조를 굴린다"는 배관 신호까지만 측정. "작가팀 수준 메인+서브를 진짜 짠다"는 미실측. 오늘 48%=타깃 잣대(생성물 대조는 미실행).

## 4. ★발견된 최대 갭 — 플래너 학습이 백지
- **판단(Critic) 학습**은 있다: loop-C 누적 DPO, per-token KL, 5축 critic(SP-E.2~E.10).
- **생성 플래너 학습**은 없다: series_arc_planner·episode_planner·payoff_scheduler·microplot_matrix는 전부 **공식 산정**. "메인+서브 16/24부작을 작가팀처럼 배분하도록 학습시키는 데이터·신호·루프" 부재.
- 산문 학습(loop-C, 토큰)과 플랜 학습(구조)은 직교 → 별도 커리큘럼 필요.

## 5. 플래너 학습 커리큘럼 (PLC) 초안
- 좌석: **PlannerPort**(신규) — FormulaPlanner→BCPlanner→DPOPlanner, GenerativePort와 직교 2층.
- 커리큘럼: **A(모방/BC)→C(공식 잔차 안전판)→B(플랜 선호 DPO)**, D(자율 자기대국)는 Phase G로 연기.
- 데이터 씨앗 = 오늘의 48% 측정. 최소 라벨(서브비율+roles+tension)은 오늘 작업+기존 공식으로 충당, affiliation/cross 라벨은 SUBPLOT-RATIO v2에서 충전.
- 첫 관문(A 1라운드 DoD): BC 플랜을 measure 스크립트로 재측정 0.46±0.10, K궤적 아크형 유지, held-out 재현.
- 산출: `docs/design/DESIGN-PLANNER-LEARNING-CURRICULUM-v1-DRAFT.md`.

## 6. 누적 발판 — 다음 의제 후보
1. PlannerPort Protocol + SeriesPlan 스키마 확정.
2. 라벨러 확장: roles 3종(반대주인공 분리) + tension/payoff 추출 패스.
3. SUBPLOT-RATIO v2: 직장군 vs 가족군 소속 유형(role NER) + 메인-서브 교차 시점.
4. (집·GPU) BCPlannerPort SFT 1라운드 → DoD 측정 = 플래너 품질 첫 객관 실측.

## 7. 사슬 요약
실측(48%) = 라벨 → 설계(AEG) = 아키텍처 → 진단 = 갭 노출 → 초안(PLC) = 학습 경로.
오늘 잰 숫자가 내일 학습의 라벨이 된다. 누적이 곧 기획이다.
