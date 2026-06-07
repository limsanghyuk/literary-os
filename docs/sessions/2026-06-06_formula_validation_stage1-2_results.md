# 공식 검증 하니스 — Stage 1·2 실행 결과 (2026-06-06)

검증 로드맵 Stage 0(하니스)+1(physics 상관)+2(DRSE 잔향) 실제 실행. 실 모듈 사용(mock 아님).
- 모듈: physics.fitness_score(NarrativeFitnessScore), drse.drse_engine(TFIDFSemanticScorer)
- 데이터: 3편(오징어게임·도깨비·나의 아저씨) × 6씬 = 18씬, LLM 생성(6 fitness 컴포넌트 + 별도 품질판정 proxy GT).

## STAGE 1 — 실 fitness 공식 vs 품질(proxy GT)
- N=18, fitness 3.60~9.68(평균 7.65/10)
- **Spearman(fitness, quality) = +0.399** (사전등록 임계 0.40 경계선)
- 컴포넌트별 vs 품질 상관:
  - motif_residue **+0.82** / reader_surface +0.62 / scene_energy +0.59 / arc_tension +0.54 / conflict +0.37 / curiosity +0.17

**발견 1 (재가중 기회)**: 종합 fitness(0.40)가 단일 최고 컴포넌트 motif_residue(0.82)보다 **약하다**. 현재 6컴포넌트 가중치가 품질과 정렬돼 있지 않다 → motif·surface·energy 쪽으로 재가중하면 타당성↑. **공식 가중치가 실데이터로 재보정 가능함을 실증.**

## STAGE 2 — DRSE 잔향(복선 plant↔payoff 의미 정합)
- 복선쌍 N=17, **평균 TFIDF sim = 0.024**(0~0.11) — 사실상 0.

**발견 2 (DRSE 한계 확인)**: TFIDF 어휘 유사도로는 복선 회수를 탐지 못한다(plant와 payoff는 어휘가 다름). 이는 코드 자체 주석('EmbeddingScorer 전환 전 보정', RESIDUE_MIN_S 폴백)과 일치 → **DRSE는 임베딩 스코어러로 전환해야 복선 검증 가능.**

## 검증됐고/안 된 것 (정직)
- ✅ 하니스 동작 + 실 공식에 실데이터 주입 + 상관 산출. 공식 문제 2건(재가중·DRSE 임베딩) 실측 발견.
- ❌ 한계: proxy GT(LLM 품질)·동일 LLM 부분 순환·N=18·TFIDF 단문 한국어 조악. 절대 타당성 아님.
- 단 발견1(종합<최고컴포넌트)은 동일 데이터 내 상대비교라 순환에 견고.

## 다음 (Stage 3~)
1. DRSE를 BGE-M3 임베딩 스코어러로 교체 후 복선 잔향 재측정.
2. fitness 가중치를 상관 구조로 재학습(physics_coefficient_updater) → 재검증.
3. 인간 작가 GT + 규모(30~50편) 확대로 절대 타당성(G_VALUE_PROOF).
