# 생성 본체 L4 구현명세 v1.0 — 7패스 오케스트레이션 (WP-5, Sonnet 집행용) (2026-06-11)

**기준선**: HEAD `8c4986b` · 선행: generation_orchestration_algorithm_v1(06-05, L3 의사코드) · 통합 지도 §4 빈칸 1
**원칙**: 신설 금지 — **기존 모듈에 배선**. 코드 앵커 실측: `orchestrators/scene_generation_orchestrator.py`(run_episode 실재)·`narrative_conductor`·`episode/episode_planner`·`rag/rag_context_builder`·`nkg/pipeline`·`render_loop/closed_loop_render`·`prose/render_orchestrator`. 검증주간 발견(쌍대·문체·안티LLM 공백) 전부 반영.

═══════════════════════════════════════════
## §1. 7패스 — 패스별 입출력 계약 + 배선
═══════════════════════════════════════════
공유 상태 = NKG 작업 메모리(패스 간 누적). 모든 계약은 `literary_system/contracts/generation.py`(신규 1파일)에 TypedDict로 정본화.

| 패스 | 입력 → 출력 (계약) | 소유 모듈 (배선) | 신규 코드 |
|---|---|---|---|
| **P0 씨앗** | `WorkBrief{premise, genre, style_profile_id, episode_count, motifs[]}` → 검증된 brief | episode/episode_planner | brief 검증기만 |
| **P1 거시** | brief → `MacroArc{act_breaks[], tension_targets[], theme}` | episode_structure_calculator | 어댑터 |
| **P2 서브플롯** | MacroArc → `SubplotPlan{threads[], plant_payoff_map[]}` — **plant_payoff_map은 P2에서 의무 생성**(LW-3: 설계된 복선만 회수 보증) | microplot_matrix + nkg/edge_infer | plant 등록 함수 |
| **P3 인물** | SubplotPlan → `CastBinding{characters[], intent_vectors[]}` | orchestrators/character_intent_agent | 어댑터 |
| **P4 씬 비트** | P1~P3 → `SceneBeat[]{beat, present[], goal, conflict, exit_state}` | orchestrators/sequence_planner | 비트 스키마 정합 |
| **P5 씬 루프** | SceneBeat → `SceneText + SceneFeature` (§2 상세) | **scene_generation_orchestrator.run_episode 확장** | 게이트 교체 |
| **P6 검증** | 에피소드 전체 → `EpisodeReport` | validation/ (WP-1·4b 산출) | 호출만 |
| **P7 선택·학습** | best-of-n + 개입 → DPO 쌍 적재 | learning/signal_schema(WP-4) | 연결만 |

═══════════════════════════════════════════
## §2. P5 씬 루프 — 검증주간 반영 핵심 수정 (L3 대비 변경점)
═══════════════════════════════════════════
```python
def generate_scene(beat, nkg, cfg) -> SceneResult:
    ctx = rag_context_builder.build(beat, nkg)                  # 기존
    drafts = []
    for i in range(cfg.best_of_n):                              # 기본 n=2 (비용)
        d = llm.write(beat, ctx, style=style_dna.compile(cfg.style_profile_id))  # 문체 지시 선반영(LW-5 입증)
        d = anti_llm_filter.filter(d).filtered                  # 후처리 (패턴 일반화 전까지 보조)
        drafts.append(d)
    # [변경1] 절대 점수 선별 금지 → 쌍대 토너먼트 (WP-4b pairwise.compare)
    best = pairwise_tournament(drafts, anchors=cfg.anchor_set)   # G_NO_ABSOLUTE_REWARD 준수
    # [변경2] 게이트 = 특성 판단 2종 (선호 질문 금지, LW-5 프로토콜)
    ok_style  = trait_check(best, trait=cfg.style_profile.trait_desc)   # 문체 달성
    ok_struct = drift_guard(best, nkg) and nkg_consistency(best, beat)  # R3 가드(기존 공식 무변경)
    if not (ok_style and ok_struct): return regenerate_or_escalate(...)  # 재생성 1회 → 개입 큐
    feat = scene_feature_extractor.extract(best)                # 기존 physics
    nkg.update(beat, best, feat)                                # plant 등장/회수 기록 의무
    return SceneResult(text=best, feature=feat, judgments=...)  # R5 근거 보존
```
- **[변경3] P6 검증**: Constitution 절대점수 게이트 → ①plant_payoff_map 회수율(NKG 정량, 미회수=부채 보고) ②씬 시퀀스 인접 일관성(LW-1 측정, 셔플 대비 백분위) ③쌍대 회귀(직전 에피소드 대비 anchor 승률). BT 점수는 보고용.
- degradation 경로(L3의 LLM 차단→공식 복귀) 유지 — 단 복귀 기준도 쌍대 승률로.

═══════════════════════════════════════════
## §3. WP-5 패키징 (권장 V764~V770)
═══════════════════════════════════════════
| WP | 내용 | 테스트(선기재) | DoD |
|---|---|---|---|
| WP-5a (V764~65) | contracts/generation.py + P0~P4 어댑터 배선 | test_contracts_roundtrip · test_p2_plant_map_required · test_p4_beat_schema | 계약 직렬화+기존 모듈 호출 green |
| WP-5b (V766~68) | P5 루프 게이트 교체(쌍대 토너먼트·trait_check·재생성 경로) | test_p5_no_absolute_selection(타입 가드) · test_trait_gate_blocks · test_drift_guard_wired · test_regenerate_then_escalate | mock LLM으로 전 경로 green |
| WP-5c (V769~70) | P6 검증 3종 + P7 DPO 적재 연결 + E2E 픽스처 1편 | test_p6_payoff_recall · test_p6_sequence_coherence · test_e2e_episode_fixture | 픽스처 에피소드 E2E green + 실키 스모크 1씬(cost_cap $0.20) |
- 의존: WP-1(validation)·WP-4b(pairwise) 선행 필수. WP-2·3과는 독립.
- 에스컬레이션·재량 범위: 기존 핸드오프 §0 규약 그대로.

## §4. 자기 점검
- best_of_n 쌍대 토너먼트의 씬당 판정 비용: n=2면 1판정 — 비용 증가 없음. n>3은 cost_cap 검토.
- trait_check도 LLM 판정 — LW-5에서 6/6였으나 박빙 영역 신뢰도는 미검증(난이도 사다리와 동일 한계). 게이트 실패 시 차단이 아니라 '개입 큐' 행으로 한 이유.
- 실제 60분 분량(수십 씬) E2E는 토큰·시간상 CI 야간 잡으로 — WP-5c DoD는 압축 픽스처로 한정.
**문서 ID**: LOS-GENCORE-L4-V1.0-2026-06-11
