# R21 38작 Drama Corpus ↔ Literary OS Retrieval / Hierarchical Planning Bridge

**Date:** 2026-08-19  
**Status:** `CURRENT_CROSS_REPO_RESEARCH_BRIDGE`  
**Data/method authority:** `limsanghyuk/v1700-literary-os`  
**Engine/experiment authority:** `limsanghyuk/literary-os`

## 1. 왜 이 브리지가 필요한가

두 저장소는 역할이 다르다.

- `v1700-literary-os`: 한국 드라마 SOURCE 직접독해, Stage01–04, Boundary, THICK, EpisodeSynopsisPlan, R5/R8, validation, DB release의 데이터/방법론 트랙.
- `literary-os`: CT 실험, 생성 엔진, candidate selection, retrieval, planning, critic, rollout, product architecture 트랙.

엔진 저장소가 과거 12작/25작/34작 상태를 자체 current truth로 유지하면 데이터 트랙과 연구 트랙이 다시 분리된다. 따라서 엔진은 드라마 corpus의 현재 수치를 복제해 독자 권위로 만들지 말고 **v1700 live pointer + artifact SHA**를 참조한다.

## 2. 현재 데이터 authority snapshot

v1700 R21 기준:
- Stage01–04: 98 works
- V10.1-equivalent: 97
- SOURCE_HOLD: 1 (`최강칠우`)
- CANONICAL THICK / Boundary / EpisodePlan: 38 works
- Stage02=THICK: 6,357=6,357
- EpisodePlanningContext: 714
- EpisodeSynopsisPlan: 714
- schema: `EpisodeSynopsisPlan.v0.3-r1`
- R5/R8: 714/714
- Runtime scenes: 46,078

Final DB:
`DB98_98WORK_STAGE04_38THICK_BOUNDARY_R1_38QUAL_EPPLAN_38WORK_CANONICAL_V03_R1_4WORK_DEEP_SEMANTIC_R2_CURRENT_AUTHORITY_CLEAN_R21_V9_20260818_FINAL_SEALED.zip`

SHA256:
`7c0cf924a5acd78d338df4f36a7626d14c290fbd6c9eadcf09bdc6ad1b8a1b49`

New-session current-only bundle:
`DRAMA_ANALYSIS_NEW_SESSION_CURRENT_ONLY_R21_38THICK_38EPPLAN_4WORK_DEEP_SEMANTIC_R2_20260818_FINAL_SEALED.zip`

SHA256:
`b932a186c195844b0c07537d4470c81df65eb12fcd621e78abf60b2a027f44e7`

## 3. 현재 EpisodeSynopsisPlan 과학 상태

CT-13 R3 external renderer:
- 48/48 sealed outputs
- renderer manifest SHA: `b9a7c420dde4c58d2c7469272aa230fb220f0cc4784e1859a83b272b804774e0`

현재 GPT 세션 내부 robustness diagnostic에서는 C(work-specific EpisodeSynopsisPlan)가 B와 mismatched N보다 P1/P2/P3에서 강하게 우세했다.

하지만 preregistration §7이 independent scorer separation을 요구하므로:
- formal verdict: **UNDECLARED**
- diagnostic: **PASS-like strong incremental utility support**
- reverse-engineered 38-work EpisodePlan corpus: **CANONICAL**
- autonomous forward EpisodePlan control: **EXPERIMENTAL_HOLD**

엔진 문서에서 이를 PASS로 과장하지 않는다.

## 4. 기존 SequencePlan / retrieval evidence

### Blind Forward 2026-08-11
`공주가돌아왔다 EP01–08→EP09`
- A: 65
- B + Stage01–04: 84
- C + THICK + PlannerInput: 88

`결혼못하는남자 EP09`
- candidate 8 → selected 6 / deferred 2
- SequencePlan quality 86
- future leakage 0
- scene draft 77 → critic/revision 86
- holdout compatibility 73
- scientific interpretation: `PASS_WITH_LIMITATIONS`

### CT-11
주판정인 canonical boundary reproduction은 균등분할 baseline을 못 이겨 불성립.
그러나:
- B−A +0.028
- **cross-work retrieval C−B +0.070** — prereg threshold +0.05 충족
- |Δ sequence count| 3.22 → C 1.67

따라서 cross-work retrieval은 좋은 초기 신호였지만 당시 boundary ceiling 문제 때문에 final proof는 아니다.

현재는 v1700에서 Boundary R1 + 38작 parity를 보강했으므로 같은 질문을 더 강한 조건에서 재시험할 가치가 크다.

## 5. 다음 연구의 중심 질문

> **미래 SOURCE 없이 N-1 state와 current drama case library만으로 모델이 EpisodeSynopsisPlan을 자율 생성하고, 그 Plan에서 congruent SequencePlans를 자율 생성하여 여러 회차를 지속 설계할 수 있는가?**

이것이 CT-13 단순 반복보다 우선한다.

## 6. Retrieval-Augmented Narrative Planning

엔진은 원작 표면을 가져오는 RAG가 아니라 **설계 기능을 검색하는 RAG**를 구현해야 한다.

Query features 예:
- relationship state
- information policy
- active debt
- thread state
- episode function
- required/deferred move
- desired terminal
- Sequence transaction type

Pipeline:
`Current State → Functional Retrieval → Multi-reference Cases → Grammar Abstraction → Story-surface Detach → Recombination → EpisodeSynopsisPlan → SequencePlans → Similarity/Leakage Audit`

single-source imitation을 기본 전략으로 사용하지 않는다.

## 7. Retrieval Scaling

다음 실험에서는 size와 depth를 분리한다.

Corpus-size arm:
`0 / 5 / 10 / 20 / 38 works`

Representation-depth arm:
`Stage02 thin / THICK / THICK+Boundary / THICK+Boundary+EpisodeSynopsisPlan`

Negative controls:
- unrelated retrieval
- mismatched plan
- high-volume but low-relevance retrieval

핵심 질문:
- 38작이 20작보다 실제 더 좋은가?
- 고품질 10작이 thin 38작보다 좋은가?
- retrieval precision이 corpus size보다 중요한가?
- context volume 자체 효과인가, relevant case effect인가?

## 8. Hierarchical planning research

### Proposed CT-14
Retrieval Scaling.

### Proposed CT-15
Blind Forward EpisodeSynopsisPlan from N-1 only.

### Proposed CT-16
Generated EpisodeSynopsisPlan → generated SequencePlans.
Cross-level congruence를 주 metric으로 추가.

### Proposed CT-17
Multi-episode rollout: generated EP09 state → EP10 → EP11 → EP12.

### Proposed CT-18
SequencePlan → ScenePlan → Beat.

### Proposed CT-19
Beat → Shot → Storyboard → Production Asset compilation.

이 번호는 현재 session roadmap 제안이며 preregistration 전에는 확정 experiment authority가 아니다.

## 9. Narrative Weighting

Literary OS의 학습 자산은 LLM 내부 neural weights와 다르게 다음 외부 weight 계층으로 발전할 수 있다.

1. Hard constraints — future leakage, Canon contradiction, SOURCE integrity, Boundary/parity, debt accounting.
2. Narrative priors — thread/debt timing, reveal, relationship pressure, terminal/rhythm.
3. Retrieval weights — function/state/debt/information/goal/position/genre relevance.
4. Candidate-ranking weights — Plan/Sequence 후보 품질 예측.
5. Dynamic Narrative Attention — work/episode-specific active Thread/axis priority.

진화:
`Explicit Rules → Measured Priors → Learned Weights → Dynamic Narrative Attention`

38작 corpus는 general LLM pretraining보다 retrieval scorer / ranker / critic / candidate selector 학습에 먼저 활용하는 것이 현실적이다.

## 10. 상업적 제품 방향

최종 제품은 “AI가 영상을 바로 만들어준다”가 아니라:

> **아이디어를 먼저 이야기로 설계하고, 그 설계를 대본·스토리보드·영상 제작 자산으로 내리는 Story Production OS**

이어야 한다.

Target descent:
`Series/Canon → EpisodeSynopsisPlan → SequencePlan → ScenePlan → Beat → Screenplay → Storyboard → Shot → Image/Video/Audio assets`

영상 모델은 교체 가능한 renderer로 두고 Narrative Intelligence를 핵심 자산으로 유지한다.

## 11. Cross-repo authority rule

Drama corpus 숫자/품질/방법론이 필요하면:
1. `limsanghyuk/v1700-literary-os/DRAMA_ANALYSIS_CURRENT_INTEGRATED_POINTER.json`을 먼저 확인한다.
2. 엔진 repo의 역사 snapshot 수치가 다르면 v1700 current가 우선한다.
3. CT 실험 결과와 preregistration은 `literary-os`가 권위다.
4. DB release artifacts는 SHA로 연결하고 대용량 ZIP 자체를 두 저장소에 중복 정본화하지 않는다.

이 브리지의 목적은 **분석 DB → Retrieval → Episode planning → Sequence planning → Scene/Beat/Storyboard**를 하나의 지속적인 개발 경로로 유지하는 것이다.
