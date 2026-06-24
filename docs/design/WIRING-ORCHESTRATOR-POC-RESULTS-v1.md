# 배선 오케스트레이터 PoC — 작업 내용·방식·결과 (v1)

날짜: 2026-06-24 / 작성: 계획·설계 모드 / 상태: **배관증명 PASS**
선행 설계: `docs/design/2026-06-24_DESIGN-LLM2-WIRING-ORCHESTRATOR-v1.md`
산출 코드: `examples/wiring_poc.py`, `examples/test_wiring_poc.py`

---

## 0. 한 줄 결론

> 그동안의 개발은 **부품(기관) 16개를 만들었지만 최상위 자율 조립 배선은 없었다.**
> 본 PoC가 그 빈칸을 메우는 **첫 실체** — 12개 실 기관을 위상정렬 순서로 연결해
> "스스로 16부작(및 24부작)을 산정·전개"하는 E2E 배관을 GPU 0회로 증명했다.

---

## 1. 왜 이 작업인가 (문제 정의)

### 1.1 감사로 드러난 사실
- `DramaEpisodeGenerator.generate_series`는 **사람이 고정한** logline·인물을 받아,
  생성 경로에서 16개 기관 중 **단 1개**(EpisodeStructureCalculator)만 호출했다.
- 나머지 12개 기관(아크 플래너·인과 그래프·payoff·지식추적·갈등충돌 등)은
  **서로 연결되지 않은 고립된 섬**이었다.
- 4기관 체인(arc→causal→reveal→knowledge)은 **게이트 테스트 스캐폴딩에만** 존재,
  실제 산문을 내보내지 않았다.
- 화별로 독립 생성되어 **화간 상태 전이(N→N+1)가 없었다.**

### 1.2 결정적 발견 — 피드백 버스는 이미 타입 정합
- 스칼라 기관의 출력이 `NarrativeStateTensor` 필드와 그대로 맞물린다:
  - `ConflictCollisionResult.conflict_intensity` → `tensor.conflict_pressure`
  - `EpisodePlan.emotional_targets` 평균 → `tensor.avg_emotional_momentum`
- 그리고 `EpisodePlanner.plan()`은 **그 텐서 필드를 읽어** K(마이크로플롯 수)를 산정한다
  (`episode_planner.py:79~90` 실측).
- 따라서 **텐서 = 통합 버스 + N→N+1 피드백 채널.**
  배선은 *0→1 발명이 아니라, 이미 맞물려 깎인 톱니를 끼우는 일*이었다.

---

## 2. 작업 방식 (어떻게 했나)

### 2.1 아키텍처 — ToT에서 선택한 안 B
| 안 | 내용 | 판정 |
|----|------|------|
| A | 중앙 갓-오브젝트 | 탈락(결합 폭발·트랙 분리 위배·과거 IO-MERGE 기각 전례) |
| C | 블랙보드/이벤트버스 | 탈락(과설계·비결정 순서가 졸업 측정 방해) |
| **B** | **스테이지 파이프라인 + 텐서 통합버스 + 얇은 어댑터 + Port 교체 좌석** | **채택** |

### 2.2 위상정렬 배선 순서 (실 시그니처 기반)
```
S1 SeriesArcPlanner.plan()              → CausalPlotGraph (인과/복선/감정 엣지 내장)
S3 EpisodeRevealBudget.from_arc_graph   → 화별 reveal 원장
S0 derive_residue_ids(graph)            ← 선결 글루 #1
S4 KnowledgeStateTracker.register_fact  → residue 사실 등록
S5 PayoffScheduler.generate_schedule    → residue 화별 배분 (압력커브 = graph 변환)
S6 SeriesConfig + NarrativeStateTensor  → 통합 버스 초기화
── 화 루프(1..N) ──
S7 PayoffScheduler.get_episode_brief    (이미 구현된 기관)
S8 EpisodePlanner.plan(cfg, idx, tensor) ← 텐서 READ (피드백 IN)
S13 GenerativePort.generate             → 생성 좌석(현재 FormulaFallbackPort)
S12 ConflictCollisionCalculus.calculate → 갈등강도
S16 tensor write-back                    → 다음 화가 읽음 (피드백 OUT)
── 루프 종료 ──
S17 MicroPlotMatrix.build(all_plans)     → 전체 누적 후 1회 (사후 패스)
```

### 2.3 선결 글루 2개 (설계서가 지목한 유일한 신규 코드)
1. **`derive_residue_ids(graph)`** — `CausalPlotGraph`에 `residue_ids` 속성이 **없음**(감사 발견).
   노드 `forbidden_reveals` ∪ FORESHADOW 엣지에서 파생, 비면 폴백.
2. **`graph_to_pressure_curve(graph)`** — 아크 `tension_curve`를 payoff 압력커브로 변환.

### 2.4 생성 좌석 (교체 가능 seam)
`GenerativePort` Protocol → 현재 `FormulaFallbackPort`(템플릿, 무GPU).
계약 불변으로 추후 `LLM1Port`(졸업한 LLM-1) → `FrontierPort`(LLM-2)로 **무수정 교체**.

---

## 3. 결과 (무엇이 증명됐나)

### 3.1 배관증명 4명제 — 전부 PASS
| 명제 | 내용 | 결과 |
|------|------|------|
| P1 | 매크로 셋업 배선(씨드→그래프→reveal/knowledge/payoff 일관) | PASS |
| P2 | 16화 전수 동일 파이프라인 통과(누락 0) | PASS |
| P3 | N→N+1 피드백(갈등강도가 텐서에 적히고 다음 화 K에 읽힘) | PASS |
| P4 | MicroPlotMatrix는 전체 plan 누적 후 루프 밖 1회 | PASS |

### 3.2 실측 신호
- **K 궤적**(화별 마이크로플롯 수): `[4,3,4,4,4,4,5,6,6,6,5,5,5,4,4,4]`
  → 중반(8~10화) 6으로 상승하는 **아크 형태** — 텐서 피드백이 K를 실제로 흔든 증거.
- **갈등압력 궤적**: `0.057 → 0.405` 단조 상승, 화마다 다른 값(피드백 채널 생존).
- **결정성**: 2회 실행 K 궤적 동일.
- **24부작**: `total_episodes=24`도 무수정 통과(plans=24) — "16 또는 24부작 자율" 주장 검증.

### 3.3 회귀 가드
`examples/test_wiring_poc.py` — 5 tests passed (16화 배관·피드백 생존·24부작·결정성·residue 비공집).

---

## 4. DoD 점검 (설계서 8항)
1. 12개 실 기관 임포트·호출 — ✔
2. 텐서 통합버스 초기화·전수 순회 — ✔
3. N→N+1 피드백 실증(갈등압력 변동) — ✔
4. residue 파생 글루 — ✔
5. graph→압력커브 글루 — ✔
6. MicroPlotMatrix 사후 1회 — ✔
7. 결정적 재현 — ✔
8. pytest 회귀 가드 — ✔ (5 passed)

---

## 5. 한계·정직한 비선언
- **산문 품질은 증명 대상이 아니다.** Port가 템플릿 마커를 반환하므로 본 PoC는
  **신호 흐름(배관)만** 증명한다. 문학적 품질은 LLM1Port 교체 후 별도 측정.
- `derive_residue_ids`의 residue는 **에피소드 파생 태그**이지 진짜 사실 ID가 아니다
  (forbidden_reveals가 기본 공집이라 폴백). 실 운용 시 인물/사건 생성기가 사실을 채워야 함.
- S9~S11(StructureCalc·SequencePlanner·CharacterIntent)·S14~S15(감정·긴장 곡선)은
  본 배관증명에서 **호출 생략** — P1~P4 증명에 불필요. 다음 라운드에서 어댑터 추가.

---

## 6. 다음 단계 (우선순위)
1. **LLM1Port 교체** — 졸업한 LLM-1을 좌석에 끼워 산문 실생성 + 품질 측정.
2. **S9~S15 어댑터 추가** — 잔여 기관을 동일 버스에 배선(계약 불변).
3. **Synopsis Assembler** — 사람 고정 logline 제거, 씨드→시놉시스 자동 생성(LLM-2 메인 빈칸).
4. **인물·사건 생성기 → residue 실 사실 주입** — 폴백 제거.

---

## Sources
- `examples/wiring_poc.py`, `examples/test_wiring_poc.py` (literary-os 허브)
- `docs/design/2026-06-24_DESIGN-LLM2-WIRING-ORCHESTRATOR-v1.md`
- 실측 시그니처: `arc/series_arc_planner.py`, `arc/causal_plot_graph.py`,
  `episode/episode_planner.py`, `episode/episode_state.py`,
  `causal_plan/payoff_scheduler.py`, `physics/conflict_collision.py`,
  `ledgers/episode_reveal_budget.py`, `world/knowledge_state_tracker.py`,
  `episode/microplot_matrix.py`
