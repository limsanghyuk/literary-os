# 명세서 — PLC 마일스톤 A1: Subplot Allocator (BC) v1

- 상위 설계: `DESIGN-PLANNER-LEARNING-CURRICULUM-v1-DRAFT.md`(A→C→B 커리큘럼) / `DESIGN-AFFILIATION-ENSEMBLE-v1.md`(AEG)
- 실측 근거: `SUBPLOT-RATIO-MEASUREMENT-v1.md`(드라마 서브플롯 중앙값 0.459) / `examples/measure_subplot_ratio.py`(라벨러)
- 성격: **구현 명세**(개발자 실행용). 무GPU 부분(스키마·라벨러·데이터셋·계약)은 본 모드가 선구현 가능, 실 BC 학습만 집 GPU.
- 범위 한정: PLC의 **첫 단위만**. K·tension·payoff 학습은 A2+ 후속. 본 단위는 **서브플롯 배분 층**만 학습으로 추가.

---

## 1. 목표 (한 문장)
기존 공식 플래너(`EpisodePlanner`)는 floor로 보존하고, 그 위에 **"각 화에서 어느 주변 인물이 얼마만큼의 분량으로 병렬 전개되는가"를 산출하는 학습된 층**을 끼워, 생성물이 실측 드라마의 서브플롯 분포(중앙값 0.46)를 재현하게 한다.

## 2. 코드 현황 grounding (실 시그니처)
```
# literary_system/episode/episode_planner.py
class EpisodePlan:  # 현 필드 — 서브플롯/소속/역할 필드 없음
    microplot_count, total_scene_budget, act_position,
    reveal_budget_per_slot, emotional_targets, conflict_weights,
    slot_functions, planning_trace
class EpisodePlanner:
    def plan(self, series_config: SeriesConfig, episode_idx: int,
             narrative_state: NarrativeStateTensor) -> EpisodePlan   # K=공식 _compute_k(...)
# examples/wiring_poc.py episode_loop(): chars[0..3] 4명 고정, planner.plan() per 화
```
→ A1은 위를 **건드리지 않고(계약 불변)** 한 층을 추가한다.

## 3. 스키마 (신규/확장)

### 3.1 AffiliationGraph (AEG에서 승계, 입력)
```python
@dataclass
class AffiliationGroup:
    kind: str                 # "work" | "family"
    members: list[str]        # 캐릭터 id
@dataclass
class AffiliationGraph:
    protagonist: str
    groups: list[AffiliationGroup]     # 직장군 + 가족군(+선택 기타)
    roles: dict[str, str]              # char -> "protagonist"|"antagonist"|"supporting"
```

### 3.2 SubplotAllocation (신규, A1 산출물)
```python
@dataclass
class SubplotAllocation:
    episode_idx: int
    active_supporting: list[str]       # 이 화에서 병렬 전개되는 주변 인물
    target_sub_share: float            # [0,1] 목표 서브플롯 대사 비중
    cross_main: bool                   # 이 화에서 서브가 메인 인과와 교차하는가
    group_focus: str                   # "work"|"family"|"mixed" 이 화 서브의 무게중심
```

### 3.3 EpisodePlan 확장 (1필드 추가, 하위호환)
```python
subplot_allocation: Optional[SubplotAllocation] = None   # None이면 기존 동작 그대로
```

## 4. PlannerPort 좌석 (신규 seam)
```python
class SubplotAllocatorPort(Protocol):
    def allocate(self, series_config, affiliation_graph,
                 base_plan: EpisodePlan, narrative_state) -> SubplotAllocation: ...
```
- `FormulaSubplotAllocator` — baseline. 규칙: 직장군/가족군에서 가용 주변 인물을 act_position에 따라 라운드로빈 배정, target_sub_share=0.46 고정, 중반부 cross_main=True 편향.
- `BCSubplotAllocator` — 학습본(본 명세 핵심). 코퍼스에서 학습한 분포로 위를 산출.
- 교체는 계약 불변(WIRING 좌석 원칙). `episode_loop()`는 `port.allocate(...)` 한 줄만 추가.

## 5. 라벨러 (오늘 스크립트 확장)
`examples/measure_subplot_ratio.py`를 확장해 **작품→회차별 GT SubplotAllocation** 추출:
| 라벨 필드 | 추출원 | 상태 |
|---|---|---|
| target_sub_share | 현 스크립트 sub_share_k4 | ✅ 그대로 |
| active_supporting | 현 스크립트 회차별 화자 집합 − 주연 top-K | ✅ 파생 가능 |
| roles 3종 | 빈도 top-2=주인공, 다음 군집=반대(휴리스틱), 잔여=주변 | △ 반대주인공 분리 휴리스틱 추가 |
| group_focus | (v2) role NER 직장/가족 유형 | ❌ v2 — A1은 "mixed" 고정 폴백 |
| cross_main | (v2) causal_plot_graph 교차 | ❌ v2 — A1은 pure_sub_scene 비율의 역으로 근사 |
산출: `learning/planner/extract_subplot_labels.py` → `data/planner/subplot_labels.jsonl`.

## 6. BC 데이터셋 빌더
- 입력 X: (시놉시스 요약 or 로그라인, AffiliationGraph, episode_idx, base_plan 요약)
- 출력 Y: GT SubplotAllocation(active_supporting 멀티핫 + target_sub_share 회귀)
- 분리: **작품 단위** train/held, held ≥250회차(누수 차단, 기존 splits 원칙 재사용).
- 산출: `learning/planner/build_bc_dataset.py` → `data/planner/{train,held}.jsonl`.

## 7. 학습 (집·GPU 또는 경량 CPU)
- 권장 1차: **경량 분류·회귀 헤드**(주변 인물 멀티핫 + sub_share 회귀). 졸업 8B 불요 → 저비용 첫 관문.
- 손실: BCE(active_supporting) + MSE(target_sub_share). 작품단위 배치.
- 후속(A2): 8B LoRA 헤드로 격상 + 시놉시스 텍스트 조건화.
- 산출: `learning/planner/train_bc_allocator.py`, 가중치 `models/planner/bc_allocator_v1.pt`.

## 8. DoD (측정 가능 관문)
1. `subplot_labels.jsonl` ≥2,000 회차, held ≥250.
2. `BCSubplotAllocator`를 `wiring_poc`에 끼워 16부작 생성 → `measure_subplot_ratio.py` 재측정 **서브비율 중앙값 0.46±0.10**.
3. held-out 회차에서 active_supporting F1 ≥ 0.6, sub_share MAE ≤ 0.12.
4. `FormulaSubplotAllocator`(baseline) 대비 잣대 적합도(|측정−0.46|) 비열위.
5. 회귀 가드 pytest ≥5 (스키마·좌석교체·DoD2 재현·결정성·held 누수0).

## 9. 작업 순서 (개발자 체크리스트)
- [ ] (무GPU·본 모드 가능) §3 스키마 + §4 Port + EpisodePlan 1필드 확장 + FormulaSubplotAllocator.
- [ ] (무GPU) §5 라벨러 확장 → subplot_labels.jsonl.
- [ ] (무GPU) §6 BC 데이터셋 빌더 → train/held.
- [ ] (GPU/CPU) §7 경량 BC 학습 1라운드.
- [ ] (검증) §8 DoD 1~5 측정 + 보고.
- [ ] (v2 합류) group_focus/cross_main 라벨 = SUBPLOT-RATIO v2(role NER) 후 재학습.

## 10. 자기점검 (명세의 약점)
1. **A1은 "누가·얼마나" 서브플롯을 배분하는지만 학습**한다. "무슨 내용"의 서브플롯인지(인과·주제 연결)는 미포함 — cross_main/group_focus가 v2로 빠진 한계.
2. **라벨 노이즈**: roles 반대주인공 분리가 휴리스틱이라 active_supporting에 잡음 유입 가능. F1 임계를 보수적으로(0.6) 둔 이유.
3. **target_sub_share 0.46 고정 baseline**이 이미 DoD2를 통과할 수 있음 → BC의 가치는 "회차별 변동·인물 선택"의 재현에서 나옴(그래서 F1·MAE를 별도 게이트로 둠).
4. 경량 헤드는 시놉시스 텍스트 의미를 못 읽음(멀티핫 위주) → A2에서 8B 조건화로 보완.
5. 본 명세는 PLC의 1/3 단계(모방)만. C(잔차)·B(선호)는 별도 명세 대상.

## 11. 한 줄 결론
어제 잰 48%가 오늘 라벨이 되고, 그 라벨이 "서브플롯 배분"이라는 첫 학습된 플래너 층을 만든다. 공식은 floor로 살리고 그 위 한 층만 학습으로 얹는, **가장 좁고 측정 가능한 첫 관문**이 본 명세다.
