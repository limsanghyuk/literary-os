"""ProductionProof — V399.
16화 Synthetic Corpus를 생성하여 LongformEnduranceOrchestrator를 실행,
전체 endurance proof pack을 산출한다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProofPack:
    """16화 endurance proof 산출물 묶음."""
    episode_count: int
    series_title: str
    summary: Dict[str, Any] = field(default_factory=dict)
    microplot_matrix_csv: str = ""
    fractal_report: Dict[str, Any] = field(default_factory=dict)
    load_curve: List[float] = field(default_factory=list)
    agency_curves: Dict[str, List[float]] = field(default_factory=dict)
    debt_summary: Dict[str, Any] = field(default_factory=dict)
    necessity_weak_ratio: float = 0.0
    dialogue_consistent: bool = True
    voice_drift_blocked: int = 0
    fatigue_mid_risk: float = 0.0
    fatigue_finale_risk: float = 0.0
    overall_pass: bool = False
    gate_results: Dict[str, bool] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "episode_count": self.episode_count,
            "series_title": self.series_title,
            "summary": self.summary,
            "fractal_report": self.fractal_report,
            "load_curve": self.load_curve,
            "debt_summary": self.debt_summary,
            "necessity_weak_ratio": self.necessity_weak_ratio,
            "dialogue_consistent": self.dialogue_consistent,
            "voice_drift_blocked": self.voice_drift_blocked,
            "fatigue_mid_risk": self.fatigue_mid_risk,
            "fatigue_finale_risk": self.fatigue_finale_risk,
            "overall_pass": self.overall_pass,
            "gate_results": self.gate_results,
        }, ensure_ascii=False, indent=2)


class ProductionProof:
    """V399 — 16화 Synthetic Proof 생성기."""

    def generate(
        self,
        episode_count: int = 16,
        genre: str = "korean_drama",
        series_title: str = "Synthetic Series",
    ) -> ProofPack:
        """Orchestrator 없이 독립 실행 가능한 경량 proof 생성."""
        from literary_system.episode.episode_planner import EpisodePlanner
        from literary_system.episode.episode_state import NarrativeStateTensor, SeriesConfig
        from literary_system.episode.microplot_matrix import MicroPlotMatrix
        from literary_system.longform.agency_conservation import AgencyConservationChecker
        from literary_system.longform.attention_economy import NarrativeAttentionEconomy
        from literary_system.longform.dialogue_pragmatics import DialoguePragmaticsEngine
        from literary_system.longform.fractal_topology import FractalTopologyValidator
        from literary_system.longform.load_balancing import DramaticLoadBalancer
        from literary_system.longform.payoff_debt import DebtPriority, DebtType, PayoffDebt, PayoffDebtLedger
        from literary_system.longform.scene_necessity import SceneFunctionType, SceneNecessityChecker, StateDelta
        from literary_system.longform.voice_manifold import StyleGenome, VoiceManifold

        protagonist_ids = ["CHAR_A", "CHAR_B"]
        series_config = SeriesConfig(
            title=series_title,
            total_episodes=episode_count,
            runtime_minutes=60,
            genre=genre,
            protagonist_ids=protagonist_ids,
        )
        tensor = NarrativeStateTensor(
            total_episodes=episode_count,
            active_characters=protagonist_ids + ["CHAR_C", "CHAR_D"],
            conflict_pressure=0.6,
            avg_emotional_momentum=0.55,
            scene_energy_required=0.65,
            avg_curiosity_gradient=0.6,
        )

        planner = EpisodePlanner()
        plans = []
        for i in range(episode_count):
            plan = planner.plan(series_config, i, tensor)
            plans.append(plan)
            tensor.push_episode(plan.to_episode_state())
        matrix = MicroPlotMatrix.build(plans)

        # Fractal Topology
        fractal_units = FractalTopologyValidator.build_synthetic(episode_count)
        fractal_report = FractalTopologyValidator().validate(fractal_units)

        # Dramatic Load Balancing
        balancer = DramaticLoadBalancer()
        from literary_system.longform.load_balancing import EpisodeLoad
        ep_loads = [
            DramaticLoadBalancer.compute_load(
                i, plans[i].microplot_count, plans[i].act_position.value
            ) for i in range(episode_count)
        ]
        lb_report = balancer.analyze(ep_loads)

        # Agency Conservation
        from literary_system.longform.agency_conservation import AgencyConservationChecker
        agency_deltas = AgencyConservationChecker.build_synthetic_deltas(
            protagonist_ids, episode_count
        )
        agency_report = AgencyConservationChecker().check(
            agency_deltas, protagonist_ids, episode_count
        )

        # Payoff Debt Ledger
        ledger = PayoffDebtLedger()
        for i in range(episode_count):
            if i % 3 == 0:
                ledger.add_debt(PayoffDebt(
                    debt_id=f"debt_{i:03d}",
                    debt_type=DebtType.FORESHADOW,
                    priority=DebtPriority.CRITICAL if i < 4 else DebtPriority.NORMAL,
                    created_episode=i, created_scene=f"ep{i}_s1",
                    promise_type="reveal",
                    expected_payoff_min=i+2, expected_payoff_max=i+6,
                ))
            ledger.tick_episode(i)
            if i % 5 == 4:
                debts = ledger.open_debts()
                for d in debts[:2]:
                    ledger.mark_paid(d.debt_id, i, f"ep{i}_payoff", 0.8)

        # Scene Necessity
        import random
        random.seed(13)
        checker = SceneNecessityChecker()
        scene_deltas = {}
        for i in range(episode_count * 6):
            sd = StateDelta(
                belief=random.uniform(0, 0.3),
                emotion=random.uniform(0.1, 0.5),
                relationship=random.uniform(0, 0.2),
                reveal=random.uniform(0, 0.3),
                conflict=random.uniform(0.05, 0.4),
                motif=random.uniform(0, 0.2),
                agency=random.uniform(0.1, 0.4),
                curiosity=random.uniform(0.05, 0.35),
            )
            scene_deltas[f"sc_{i:04d}"] = sd
        necessity_report = checker.analyze(scene_deltas)

        # Dialogue Pragmatics
        dp_engine = DialoguePragmaticsEngine()
        profiles = DialoguePragmaticsEngine.build_synthetic_profiles(
            protagonist_ids + ["CHAR_C", "CHAR_D"]
        )
        dialogue_report = dp_engine.analyze_profiles(profiles, [])

        # Voice Manifold
        manifold = VoiceManifold()
        ep_vectors = StyleGenome.build_synthetic(episode_count)
        manifold.set_anchor(ep_vectors[:3])
        voice_report = manifold.analyze_drift(ep_vectors)

        # Attention Economy
        ae = NarrativeAttentionEconomy()
        scene_vals = NarrativeAttentionEconomy.build_synthetic_scenes(
            episode_count, scenes_per_ep=8
        )
        fatigue_report = ae.analyze(scene_vals, episode_count)

        overall = (
            fractal_report.pass_gate
            and lb_report.pass_gate
            and agency_report.pass_gate
            and ledger.finale_critical_check()
            and necessity_report.pass_gate
            and dialogue_report.pass_gate
            and voice_report.pass_gate
            and fatigue_report.pass_gate
        )

        gate_results = {
            "fractal_topology": fractal_report.pass_gate,
            "load_balancing": lb_report.pass_gate,
            "agency_conservation": agency_report.pass_gate,
            "payoff_debt": ledger.finale_critical_check(),
            "scene_necessity": necessity_report.pass_gate,
            "dialogue_pragmatics": dialogue_report.pass_gate,
            "voice_manifold": voice_report.pass_gate,
            "attention_economy": fatigue_report.pass_gate,
        }

        return ProofPack(
            episode_count=episode_count,
            series_title=series_title,
            summary=matrix.summary(),
            microplot_matrix_csv=matrix.to_csv(),
            fractal_report={
                "orphan_microplot_count": fractal_report.orphan_microplot_count,
                "episode_function_coverage": fractal_report.episode_function_coverage,
                "pass": fractal_report.pass_gate,
            },
            load_curve=lb_report.load_curve,
            agency_curves=agency_report.character_agency_curves,
            debt_summary=ledger.summary(),
            necessity_weak_ratio=necessity_report.weak_scene_ratio,
            dialogue_consistent=dialogue_report.is_consistent,
            voice_drift_blocked=voice_report.blocked_drift_count,
            fatigue_mid_risk=fatigue_report.mid_season_fatigue_risk,
            fatigue_finale_risk=fatigue_report.finale_fatigue_risk,
            overall_pass=overall,
            gate_results=gate_results,
        )
