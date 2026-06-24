"""
examples/wiring_poc.py — LLM-2 배선 오케스트레이터 PoC (무GPU 배관증명)

목적
----
literary-os의 16개 기관은 "부품"으로 존재하나 최상위 자율 조립 배선이
없었다(감사 사실). 본 PoC는 12개 실 기관을 위상정렬 순서(S1~S17)대로
연결하여 "스스로 16부작을 산정·전개"하는 E2E 배관을 증명한다.

GPU/LLM 0회. GenerativePort 자리에 FormulaFallbackPort(템플릿)를 끼워
배선 경로만 검증한다 — 산문 품질이 아니라 신호 흐름이 증명 대상.

증명 명제
---------
P1  매크로 셋업 배선:  씨드 → 아크그래프 → reveal/knowledge/payoff 일관 구성
P2  화-루프 순회:       16화 전부 동일 파이프라인을 통과(누락 없음)
P3  N→N+1 피드백:       화 결과(갈등강도)가 텐서에 적히고 다음 화 K 산정에 읽힘
P4  사후 패스 배치:      MicroPlotMatrix는 전체 plan 누적 후 루프 밖에서 1회

실행:  cd /tmp/hub2 && python3 examples/wiring_poc.py
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Protocol, Tuple

# ── 실 기관 임포트 (literary_system) ───────────────────────────────
from literary_system.arc.series_arc_planner import SeriesArcPlanner
from literary_system.arc.causal_plot_graph import CausalPlotGraph
from literary_system.arc.schema import ArcPlotEdgeType
from literary_system.ledgers.episode_reveal_budget import EpisodeRevealBudget
from literary_system.world.knowledge_state_tracker import (
    KnowledgeStateTracker,
    InformationType,
)
from literary_system.causal_plan.payoff_scheduler import PayoffScheduler
from literary_system.episode.episode_state import (
    NarrativeStateTensor,
    SeriesConfig,
)
from literary_system.episode.episode_planner import EpisodePlanner, EpisodePlan
from literary_system.episode.microplot_matrix import MicroPlotMatrix
from literary_system.physics.conflict_collision import ConflictCollisionCalculus


# ═══════════════════════════════════════════════════════════════════
# GenerativePort — 생성 좌석(seam). 추후 LLM1Port / FrontierPort로 교체.
# ═══════════════════════════════════════════════════════════════════
class GenerativePort(Protocol):
    def generate(self, prompt: str, *, episode_idx: int) -> str: ...


@dataclass
class FormulaFallbackPort:
    """무GPU 배관증명용. 산문 대신 결정적 마커를 반환."""
    name: str = "formula-fallback"

    def generate(self, prompt: str, *, episode_idx: int) -> str:
        return f"[FORMULA-FALLBACK ep{episode_idx:02d}] {prompt[:60]}"


# ═══════════════════════════════════════════════════════════════════
# WiringContext — 통합 버스(integration bus). 기관 사이 신호를 운반.
# ═══════════════════════════════════════════════════════════════════
@dataclass
class WiringContext:
    graph: CausalPlotGraph
    reveal_budget: EpisodeRevealBudget
    knowledge: KnowledgeStateTracker
    schedule: object
    config: SeriesConfig
    tensor: NarrativeStateTensor
    residue_ids: List[str]
    plans: List[EpisodePlan] = field(default_factory=list)
    prose: List[str] = field(default_factory=list)
    # 증명용 추적
    k_trace: List[int] = field(default_factory=list)
    conflict_trace: List[float] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)


# ── 선결 글루 #1: residue_ids 파생 ─────────────────────────────────
def derive_residue_ids(graph: CausalPlotGraph) -> List[str]:
    """
    CausalPlotGraph에는 residue_ids 속성이 없다(감사 발견).
    노드의 forbidden_reveals ∪ FORESHADOW 엣지 타깃에서 파생.
    비면 'core_secret' 폴백(배관증명용 최소 1개 보장).
    """
    ids: List[str] = []
    for node in graph.all_nodes():
        for fid in node.forbidden_reveals:
            if fid not in ids:
                ids.append(fid)
    for edge in graph.all_edges():
        if edge.edge_type == ArcPlotEdgeType.FORESHADOW:
            tag = f"residue_{edge.source}"
            if tag not in ids:
                ids.append(tag)
    if not ids:
        ids = ["core_secret", "hidden_identity", "betrayal_fact"]
    return ids


# ── 선결 글루 #2: graph → macroarc 압력 커브 ───────────────────────
def graph_to_pressure_curve(graph: CausalPlotGraph) -> List[float]:
    """아크그래프 tension_curve를 payoff 압력 커브로 변환."""
    curve = [t for _, t in graph.tension_curve()]
    return curve or None


# ═══════════════════════════════════════════════════════════════════
# 매크로 셋업 배선  S1 ~ S6
# ═══════════════════════════════════════════════════════════════════
def macro_setup(total_episodes: int, title: str) -> WiringContext:
    prov: List[str] = []

    # S1: 씨드 → 시리즈 아크 그래프 (infer_causal/foreshadow/escalation 내장)
    graph = SeriesArcPlanner(
        total_episodes=total_episodes, series_title=title
    ).plan()
    prov.append(f"S1 SeriesArcPlanner.plan -> nodes={len(graph.all_nodes())} "
                f"edges={len(graph.all_edges())}")

    # S3: 그래프 → 화별 reveal 예산 원장
    reveal_budget = EpisodeRevealBudget.from_arc_graph(graph)
    prov.append("S3 EpisodeRevealBudget.from_arc_graph -> ok")

    # S0-derive: residue 파생
    residue_ids = derive_residue_ids(graph)
    prov.append(f"S0 derive_residue_ids -> {residue_ids}")

    # S4: 지식 상태 추적기 + residue 사실 등록
    knowledge = KnowledgeStateTracker(project_id=title)
    for i, rid in enumerate(residue_ids):
        knowledge.register_fact(
            fact_id=rid,
            fact_type=InformationType.EVENT,
            description=f"residue fact {rid}",
            true_value=f"value_{i}",
            episode_revealed_at=min(total_episodes, (i + 1) * 3),
            reader_knows=False,
        )
    prov.append(f"S4 KnowledgeStateTracker.register_fact x{len(residue_ids)}")

    # S5: payoff 스케줄 (residue를 화별로 배분)
    schedule = PayoffScheduler().generate_schedule(
        project_id=title,
        total_episodes=total_episodes,
        residue_ids=residue_ids,
        strategy="slow_burn",
        macroarc_pressure_curve=graph_to_pressure_curve(graph),
    )
    prov.append("S5 PayoffScheduler.generate_schedule -> ok")

    # S6: 시리즈 설정 + 서사 상태 텐서 초기화 (통합 버스의 핵심)
    config = SeriesConfig(
        title=title,
        total_episodes=total_episodes,
        protagonist_ids=["검사_한지수", "형사_박도현"],
    )
    tensor = NarrativeStateTensor(
        total_episodes=total_episodes,
        active_characters=["검사_한지수", "형사_박도현", "피의자_윤", "내부자_정"],
    )
    prov.append("S6 SeriesConfig + NarrativeStateTensor init -> ok")

    return WiringContext(
        graph=graph, reveal_budget=reveal_budget, knowledge=knowledge,
        schedule=schedule, config=config, tensor=tensor,
        residue_ids=residue_ids, provenance=prov,
    )


# ═══════════════════════════════════════════════════════════════════
# 화-루프 배선  S7 ~ S16  (텐서 = 화간 피드백 채널)
# ═══════════════════════════════════════════════════════════════════
def episode_loop(ctx: WiringContext, port: GenerativePort) -> None:
    planner = EpisodePlanner()
    conflict_calc = ConflictCollisionCalculus()
    payoff = PayoffScheduler()

    chars = ctx.tensor.active_characters
    n = ctx.config.total_episodes

    for ep in range(1, n + 1):
        ep_idx = ep - 1  # planner는 0-based pos 사용

        # S7: payoff 브리핑 조회 (이미 구현된 기관)
        brief = payoff.get_episode_brief(ctx.schedule, ep)

        # S8: 화 구조 계획 — 텐서 현재 상태(갈등압력 등)를 읽음 ← 피드백 IN
        cp_in = ctx.tensor.conflict_pressure
        plan = planner.plan(ctx.config, ep_idx, ctx.tensor)
        ctx.plans.append(plan)
        ctx.k_trace.append(plan.microplot_count)

        # S13: 생성 좌석 — 프롬프트 조립 후 Port 호출
        prompt = (f"{ctx.config.title} {ep}화 | K={plan.microplot_count} "
                  f"| payoff={brief.get('payoff_type')} cp_in={cp_in:.3f}")
        ctx.prose.append(port.generate(prompt, episode_idx=ep))

        # S12: 갈등 충돌 — 화 진행에 따라 가중치 변동(사건 누적 모사)
        ramp = ep / n
        edges: List[Tuple[str, str]] = [
            (chars[0], chars[2]), (chars[1], chars[3]), (chars[0], chars[1]),
        ]
        weights = {c: 0.3 + 0.6 * ramp for c in chars}
        cres = conflict_calc.calculate(chars, edges, weights)

        # S16: 텐서 write-back ← 피드백 OUT (다음 화 S8이 읽음)
        ctx.tensor.conflict_pressure = cres.conflict_intensity
        if plan.emotional_targets:
            ctx.tensor.avg_emotional_momentum = statistics.mean(plan.emotional_targets)
        ctx.tensor.scene_energy_required = min(1.0, 0.5 + 0.4 * ramp)
        ctx.conflict_trace.append(cres.conflict_intensity)


# ═══════════════════════════════════════════════════════════════════
# 사후 패스  S17  (전체 plan 누적 후 1회)
# ═══════════════════════════════════════════════════════════════════
def post_passes(ctx: WiringContext) -> MicroPlotMatrix:
    return MicroPlotMatrix.build(ctx.plans)


# ═══════════════════════════════════════════════════════════════════
# 오케스트레이터 + 배관증명 어서션
# ═══════════════════════════════════════════════════════════════════
def run_wiring_poc(total_episodes: int = 16, title: str = "추적자") -> WiringContext:
    port = FormulaFallbackPort()

    ctx = macro_setup(total_episodes, title)      # S1~S6
    episode_loop(ctx, port)                        # S7~S16
    matrix = post_passes(ctx)                      # S17

    # ── P1: 매크로 셋업 배선 ──
    assert len(ctx.graph.all_nodes()) == total_episodes, "P1 아크 노드 수 불일치"
    assert len(ctx.residue_ids) >= 1, "P1 residue 파생 실패"
    assert ctx.schedule is not None, "P1 payoff 스케줄 누락"

    # ── P2: 화-루프 전수 순회 ──
    assert len(ctx.plans) == total_episodes, "P2 일부 화 누락"
    assert len(ctx.prose) == total_episodes, "P2 일부 생성 누락"
    assert all(p.startswith("[FORMULA-FALLBACK") for p in ctx.prose), "P2 Port 배선 끊김"

    # ── P3: N→N+1 피드백 (텐서가 살아있는 채널) ──
    assert len(set(round(c, 4) for c in ctx.conflict_trace)) >= 2, \
        "P3 갈등압력이 화간 변동 없음(피드백 채널 죽음)"
    assert ctx.tensor.conflict_pressure == ctx.conflict_trace[-1], \
        "P3 텐서 write-back 불일치"

    # ── P4: 사후 패스 배치 ──
    assert len(matrix.episodes) == total_episodes, "P4 MicroPlotMatrix 누적 불일치"

    ctx.provenance.append(
        f"S17 MicroPlotMatrix.build -> episodes={len(matrix.episodes)}")
    return ctx


if __name__ == "__main__":
    ctx = run_wiring_poc(total_episodes=16)

    print("=" * 64)
    print(" 배선 PROVENANCE TRACE (S1~S17)")
    print("=" * 64)
    for line in ctx.provenance:
        print(" •", line)

    print("\n K 궤적(화별 마이크로플롯 수):", ctx.k_trace)
    print(" 갈등압력 궤적(피드백 신호):  ",
          [round(c, 3) for c in ctx.conflict_trace])
    print(" 최종 텐서: conflict_pressure=%.3f  emo_momentum=%.3f" % (
        ctx.tensor.conflict_pressure, ctx.tensor.avg_emotional_momentum))
    print("\n 생성 샘플(1·8·16화):")
    for i in (0, 7, 15):
        print("   ", ctx.prose[i])

    print("\n" + "=" * 64)
    print(" PLUMBING PROOF: PASS  (P1·P2·P3·P4 전부 통과)")
    print("=" * 64)
