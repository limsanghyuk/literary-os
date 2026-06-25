# 설계도: 소속군 앙상블 생성기 + 병행 서브플롯 스케줄러 v1
## Affiliation Ensemble Generator (AEG) — 인물 생성의 평면성 제거

- **작성**: 2026-06-25 (Cowork 기획·설계 모드)
- **정초 데이터**: `SUBPLOT-RATIO-MEASUREMENT-v1` (드라마 122편 실측 — 주변 인물 = 화당 대사 평균 48%)
- **트랙**: 메인 트랙(LLM-2 인물·사건 생성 자율화). 제품전략 B와 무관.
- **갭**: 현재 `wiring_poc.py`는 활성 인물 4인(주인공 2 + 적대 2)만 하드코딩 → 실측된 드라마 한 화의 절반(주변 서브플롯)이 생성 대상에서 누락.

---

## 1. 문제 정의 (구조적)

대부분의 AI는 주인공 단독의 평면적 이야기만 구성한다. 실제 드라마는 주인공을 생성하면 **반드시
그가 속한 두 집단** — ① 일(회사/직장/학교 등 직업군), ② 가족 — 의 주변 인물을 함께 생성하고,
그들의 이야기를 **병행 서브플롯**으로 운용한다. 본 설계는 이 누락층을 1급 생성 구조로 끌어올린다.

**설계 불변식 (실측 근거)**:
- I-AEG-1: 모든 주연(protagonist/antagonist)은 ≥1개의 **직업 소속군**과 **가족 소속군**을 가진다.
- I-AEG-2: 화별 씬 예산의 **40~50%(드라마) / 20~30%(영화)**를 주변 인물 서브플롯에 할당한다.
- I-AEG-3: 주연이 한 명도 없는 **순수 서브플롯 씬**이 화별로 존재해야 한다(실측 드라마 평균 24%).
- I-AEG-4: 모든 서브플롯은 ≥1회 메인 플롯과 **교차(intersection)**하여 causal_plot_graph에 환류한다.

---

## 2. 자료 구조 — Affiliation Graph (신규 1급 스키마)

기존 `character_ledger`(role_type: lead/foil 2종)를 확장. 신규 필드/엔티티:

```
AffiliationGroup:
  group_id        : str            # "직장_원인터내셔널", "가족_장그래"
  kind            : enum {work, family, school, ...}
  anchor_char_id  : str            # 이 군이 매달린 주연
  members         : [char_id]      # 주변 인물들
  internal_conflict_seed : str     # 군 내부 갈등 씨앗(서브플롯 동력)

Character (확장):
  role_type : enum {protagonist, antagonist, supporting}   # 3종으로 격상
  affiliations : [group_id]
  subplot_id  : str | null         # 주변 인물이 이끄는 서브플롯
```

**Ensemble 정의**: `ensemble = ∪(protagonist 소속군) ∪ ∪(antagonist 소속군)`.
주연마다 work-cluster + family-cluster를 생성 → 평균 주변 인물 수는 실측 화자 분포(미생 116, 시그널 191)로 캘리브레이션.

---

## 3. AEG 파이프라인 (I/O 계약)

```
generate_affiliation_ensemble(
    protagonists: [Character],     # 기존 birth_gate/intent_agent 산출
    antagonists:  [Character],
    project_context: ProjectContext,   # 장르·배경·시대
    target_media: enum {drama, film},
) -> EnsemblePlan

EnsemblePlan:
  groups        : [AffiliationGroup]      # 직장군 + 가족군 (주연별)
  supporting    : [Character]             # role_type=supporting
  subplots      : [Subplot]               # 주변 인물 주도 서브플롯
  budget        : SubplotBudget           # 화별 할당 (I-AEG-2)
```

생성 4단계:
1. **소속군 도출**: 주연의 직업/배경(project_context)에서 work-group을, 관계 시드에서 family-group을 인스턴스화.
2. **주변 인물 충원**: 각 군에 역할 슬롯(상사·동료·라이벌 / 부모·형제·배우자) 채움. 기존
   `pressure_cast_planner`(분석형)를 역방향으로 — 분석이 아니라 **생성** 모드로 호출.
3. **서브플롯 시드**: 각 군의 internal_conflict_seed → Subplot 객체(자체 K 미시플롯 보유).
4. **예산 배정**: target_media에 따라 I-AEG-2 비율로 SubplotBudget 산정.

---

## 4. 병행 서브플롯 스케줄러 (Parallel Subplot Scheduler)

EpisodePlanner의 scene_budget을 **메인:앙상블**로 분할:

```
schedule_subplots(
    episode_plan: EpisodePlan,        # 기존 K, scene_budget, emotional_targets
    ensemble: EnsemblePlan,
) -> EpisodeSceneSlots

규칙:
- main_slots     = round(scene_budget * (1 - budget.supporting_ratio))
- subplot_slots  = scene_budget - main_slots             # 실측 40~50%(드라마)
- pure_subplot_slots ≥ scene_budget * 0.20 (드라마)       # I-AEG-3 (주연 부재 씬)
- 각 활성 서브플롯은 화별 ≥1 씬, 아크 진행도 단조 증가
- intersection_slots: 서브플롯이 메인과 만나는 씬 ≥1/서브플롯/아크 (I-AEG-4)
```

출력은 wiring 오케스트레이터의 S7~S17 화 루프에 주입 — `active_characters`가 4인 고정이 아니라
**화별 main∪subplot 캐스트**로 동적 구성된다.

---

## 5. 환류 — causal_plot_graph 교차 + 수정 전파 훅

- **교차(I-AEG-4)**: 각 Subplot은 메인 플롯 노드와 교차 엣지를 가진다(예: 직장 동료의 비리가
  주인공 사건의 단서가 됨). 교차점은 `causal_plot_graph`에 새 노드/엣지로 환원되어 전역 일관성 유지.
- **수정 전파 훅**: 작가가 주변 인물/서브플롯을 수정·추가하면(human-in-the-loop), 교차 엣지를 통해
  영향받는 메인 플롯 노드를 식별 → 기존 수정 전파 엔진(제품 비전)으로 재창작 트리거.

---

## 6. 배선 순서 (기존 PoC 위에)

| 단계 | 작업 | 의존 |
|---|---|---|
| AEG-1 | character_ledger role_type 3종 격상 + AffiliationGroup 스키마 | 없음 |
| AEG-2 | generate_affiliation_ensemble (§3 1~4) FormulaFallback 버전 | AEG-1 |
| AEG-3 | schedule_subplots (§4) + wiring_poc active_characters 동적화 | AEG-2 |
| AEG-4 | causal_plot_graph 교차 엣지 + 수정 전파 훅 | AEG-3 |
| AEG-5 | E2E 배관증명: 16화에서 주변 대사 점유율이 실측 40~50% 재현되는지 검증 | AEG-4 |

**DoD**: AEG-5에서 생성된 16화의 주변 대사 점유율을 `measure_subplot_ratio.py`로 재측정했을 때
실측 드라마 분포(median 0.46) ±0.10 안에 들면 통과. 즉 **측정 도구가 곧 생성기의 인수 기준**이 된다.

---

## 7. 한계·후속

- 본 v1은 FormulaFallback(무 GPU) 결정론 버전 설계. 의미 충전(인물 성격·서브플롯 내용)은 LLM-2 단계 GenerativePort로 이양.
- 소속군을 직장 vs 가족으로 데이터에서 직접 분류하는 측정(SUBPLOT-RATIO v2, 역할 NER)이 AEG-1 스키마를 더 정밀하게 정초할 것 — 후속 측정 권고.
