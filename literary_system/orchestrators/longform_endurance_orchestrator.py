"""LongformEnduranceOrchestrator — V399.
Gate 1~8 (V390) + 8개 장편 이론 모듈 (V393~V398)을
16화 전체 파이프라인으로 통합하는 최상위 오케스트레이터.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.episode.episode_planner import EpisodePlanner
from literary_system.episode.episode_state import NarrativeStateTensor, SeriesConfig
from literary_system.episode.microplot_matrix import MicroPlotMatrix
from literary_system.longform.agency_conservation import AgencyConservationChecker, AgencyDelta, AgencyReport
from literary_system.longform.attention_economy import FatigueReport, NarrativeAttentionEconomy
from literary_system.longform.dialogue_pragmatics import DialoguePragmaticsEngine, DialogueReport
from literary_system.longform.fractal_plot_tree import (
    FractalPlotTree,
    FractalPlotTreeBuilder,
    FractalTreeConfig,
)
from literary_system.longform.fractal_topology import FractalReport, FractalTopologyValidator
from literary_system.longform.load_balancing import DramaticLoadBalancer, EpisodeLoad, LoadBalanceReport
from literary_system.longform.payoff_debt import PayoffDebtLedger
from literary_system.longform.scene_necessity import NecessityReport, SceneNecessityChecker, StateDelta
from literary_system.longform.voice_manifold import StyleGenome, VoiceDriftReport, VoiceManifold


@dataclass
class LongformInput:
    """LongformEnduranceOrchestrator의 입력."""
    series_config: SeriesConfig
    # 선택적 사전 데이터 (없으면 synthetic 생성)
    agency_deltas: Optional[List[AgencyDelta]] = None
    narrative_state: Optional[NarrativeStateTensor] = None


@dataclass
class EnduranceRunReport:
    """LongformEnduranceOrchestrator 실행 결과."""
    series_title: str
    episode_count: int
    microplot_matrix: Optional[MicroPlotMatrix] = None
    fractal_report: Optional[FractalReport] = None
    fractal_tree: Optional[FractalPlotTree] = None  # V556: FractalPlotTreeBuilder 연결
    load_report: Optional[LoadBalanceReport] = None
    agency_report: Optional[AgencyReport] = None
    debt_ledger: Optional[PayoffDebtLedger] = None
    necessity_report: Optional[NecessityReport] = None
    dialogue_report: Optional[DialogueReport] = None
    voice_drift_report: Optional[VoiceDriftReport] = None
    fatigue_report: Optional[FatigueReport] = None
    physics_snapshots: "List[Any]" = field(default_factory=list)   # V405: PhysicsSnapshot list
    overall_pass: bool = False
    gate_summary: Dict[str, bool] = field(default_factory=dict)
    execution_trace: List[str] = field(default_factory=list)

    def add_trace(self, msg: str) -> None:
        self.execution_trace.append(msg)


class LongformEnduranceOrchestrator:
    """V399 — 최상위 장편 지속성 오케스트레이터.

    파이프라인:
    EpisodePlanner → FractalTopology → LoadBalancing
    → AgencyConservation → PayoffDebt → SceneNecessity
    → DialoguePragmatics → VoiceManifold → AttentionEconomy
    → EnduranceSummary
    """

    def run(self, inp: LongformInput) -> EnduranceRunReport:
        cfg = inp.series_config
        n = cfg.total_episodes
        report = EnduranceRunReport(series_title=cfg.title, episode_count=n)
        report.add_trace(f"START LongformEnduranceOrchestrator: {cfg.title} ({n}화)")

        # ── 1. EpisodePlanner ──────────────────────────────────────────
        tensor = inp.narrative_state or NarrativeStateTensor(
            total_episodes=n,
            active_characters=cfg.protagonist_ids + ["CHAR_C", "CHAR_D"],
            conflict_pressure=0.6,
            avg_emotional_momentum=0.55,
            scene_energy_required=0.65,
            avg_curiosity_gradient=0.6,
        )
        planner = EpisodePlanner()
        plans = []
        for i in range(n):
            plan = planner.plan(cfg, i, tensor)
            plans.append(plan)
            tensor.push_episode(plan.to_episode_state())
        matrix = MicroPlotMatrix.build(plans)
        report.microplot_matrix = matrix
        report.add_trace(f"EpisodePlanner: matrix built K_avg={matrix.summary().get('k_avg')}")

        # ── 2. Fractal Topology ────────────────────────────────────────
        fractal_units = FractalTopologyValidator.build_synthetic(n)
        fractal_report = FractalTopologyValidator().validate(fractal_units)
        report.fractal_report = fractal_report
        report.add_trace(f"FractalTopology: orphan={fractal_report.orphan_microplot_count} pass={fractal_report.pass_gate}")

        # V556: FractalPlotTreeBuilder.build() — 실제 프랙탈 트리 생성
        tree_config = FractalTreeConfig(
            total_episodes=n,
            microplots_per_episode=int(matrix.summary().get('k_avg', 4)) if matrix else 4,
        )
        report.fractal_tree = FractalPlotTreeBuilder().build(tree_config)
        report.add_trace(f"FractalPlotTree: depth={report.fractal_tree.config.max_depth} units={len(report.fractal_tree.all_units)}")

        # ── 3. Dramatic Load Balancing ─────────────────────────────────
        ep_loads = [
            DramaticLoadBalancer.compute_load(
                i, plans[i].microplot_count, plans[i].act_position.value
            ) for i in range(n)
        ]
        lb_report = DramaticLoadBalancer().analyze(ep_loads)
        report.load_report = lb_report
        report.add_trace(f"LoadBalancing: overloaded={lb_report.overloaded_episodes} pass={lb_report.pass_gate}")

        # ── 4. Agency Conservation ─────────────────────────────────────
        deltas = inp.agency_deltas or AgencyConservationChecker.build_synthetic_deltas(
            cfg.protagonist_ids, n
        )
        agency_report = AgencyConservationChecker().check(deltas, cfg.protagonist_ids, n)
        report.agency_report = agency_report
        report.add_trace(f"AgencyConservation: floor_pass={agency_report.protagonist_floor_pass}")

        # ── 5. Payoff Debt Ledger ──────────────────────────────────────
        from literary_system.longform.payoff_debt import DebtPriority, DebtType, PayoffDebt
        ledger = PayoffDebtLedger()
        for i in range(n):
            if i % 3 == 0:
                ledger.add_debt(PayoffDebt(
                    debt_id=f"auto_debt_{i:03d}",
                    debt_type=DebtType.FORESHADOW,
                    priority=DebtPriority.CRITICAL if i < 4 else DebtPriority.NORMAL,
                    created_episode=i, created_scene=f"ep{i}_s1",
                    promise_type="foreshadow_reveal",
                    expected_payoff_min=i+2, expected_payoff_max=min(n-1, i+6),
                ))
            ledger.tick_episode(i)
            for d in ledger.open_debts()[:2]:
                if i >= d.expected_payoff_min:
                    ledger.mark_paid(d.debt_id, i, f"ep{i}_payoff", 0.8)
        report.debt_ledger = ledger
        report.add_trace(f"PayoffDebt: summary={ledger.summary()} finale_ok={ledger.finale_critical_check()}")

        # ── 6. Scene Necessity ─────────────────────────────────────────
        import random
        random.seed(13)
        scene_deltas = {
            f"sc_{i:04d}": StateDelta(
                belief=random.uniform(0, 0.3), emotion=random.uniform(0.1, 0.5),
                relationship=random.uniform(0, 0.2), reveal=random.uniform(0, 0.3),
                conflict=random.uniform(0.05, 0.4), motif=random.uniform(0, 0.2),
                agency=random.uniform(0.1, 0.4), curiosity=random.uniform(0.05, 0.35),
            ) for i in range(n * 6)
        }
        necessity_report = SceneNecessityChecker().analyze(scene_deltas)
        report.necessity_report = necessity_report
        report.add_trace(f"SceneNecessity: weak_ratio={necessity_report.weak_scene_ratio:.3f} pass={necessity_report.pass_gate}")

        # ── 7. Dialogue Pragmatics ─────────────────────────────────────
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(
            cfg.protagonist_ids + ["CHAR_C", "CHAR_D"]
        )
        dialogue_report = DialoguePragmaticsEngine().analyze_profiles(profiles, [])
        report.dialogue_report = dialogue_report
        report.add_trace(f"DialoguePragmatics: consistent={dialogue_report.is_consistent}")

        # ── 8. Voice Manifold ─────────────────────────────────────────
        manifold = VoiceManifold()
        ep_vectors = StyleGenome.build_synthetic(n)
        manifold.set_anchor(ep_vectors[:3])
        voice_report = manifold.analyze_drift(ep_vectors)
        report.voice_drift_report = voice_report
        report.add_trace(f"VoiceManifold: blocked={voice_report.blocked_drift_count} pass={voice_report.pass_gate}")

        # ── 9. Attention Economy ───────────────────────────────────────
        scene_vals = NarrativeAttentionEconomy.build_synthetic_scenes(n, scenes_per_ep=8)
        fatigue_report = NarrativeAttentionEconomy().analyze(scene_vals, n)
        report.fatigue_report = fatigue_report
        report.add_trace(f"AttentionEconomy: mid_risk={fatigue_report.mid_season_fatigue_risk:.3f} pass={fatigue_report.pass_gate}")

        # ── 10. 종합 판정 ─────────────────────────────────────────────
        gate_summary = {
            "episode_layer": matrix.episode_count > 0,
            "fractal_topology": fractal_report.pass_gate,
            "load_balancing": lb_report.pass_gate,
            "agency_conservation": agency_report.pass_gate,
            "payoff_debt": ledger.finale_critical_check(),
            "scene_necessity": necessity_report.pass_gate,
            "dialogue_pragmatics": dialogue_report.pass_gate,
            "voice_manifold": voice_report.pass_gate,
            "attention_economy": fatigue_report.pass_gate,
        }
        report.gate_summary = gate_summary
        report.overall_pass = all(gate_summary.values())
        report.add_trace(f"DONE: overall_pass={report.overall_pass} gates={sum(gate_summary.values())}/{len(gate_summary)}")

        return report
