"""V360: NKGGuardrails — GR-01~GR-05 5규칙."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

class GuardrailViolation(Exception):
    def __init__(self, rule: str, msg: str): super().__init__(f"[{rule}] {msg}"); self.rule = rule; self.msg = msg

@dataclass
class GuardrailCheck:
    rule: str; passed: bool; message: str

class NKGGuardrails:
    @staticmethod
    def check_gr01_impact_required(impact_analysis_run: bool, target_nodes: List[str],
                                    shared_nodes: List[str]) -> GuardrailCheck:
        shared = [n for n in target_nodes if n in shared_nodes]
        passed = impact_analysis_run or not shared
        msg = "OK" if passed else f"공유 노드 {shared} 수정 시 영향 분석 필수"
        return GuardrailCheck("GR-01", passed, msg)

    @staticmethod
    def check_gr02_rename_dry_run(rename_requested: bool, dry_run_completed: bool) -> GuardrailCheck:
        passed = (not rename_requested) or dry_run_completed
        msg = "OK" if passed else "이름 변경 전 rename_dry_run() 필수"
        return GuardrailCheck("GR-02", passed, msg)

    @staticmethod
    def check_gr03_blast_radius(blast_ratio: float, threshold: float = 0.30) -> GuardrailCheck:
        passed = blast_ratio <= threshold
        msg = "OK" if passed else f"Blast Radius {blast_ratio:.1%} > 임계값 {threshold:.1%}"
        return GuardrailCheck("GR-03", passed, msg)

    @staticmethod
    def check_gr04_semantic_frozen(is_frozen: bool) -> GuardrailCheck:
        passed = is_frozen
        msg = "OK" if passed else "VERIFY 단계 진입 전 SemanticModel FROZEN 필수"
        return GuardrailCheck("GR-04", passed, msg)

    @staticmethod
    def check_gr05_detect_changes(multi_scene_edit: bool, changes_detected: bool) -> GuardrailCheck:
        passed = (not multi_scene_edit) or changes_detected
        msg = "OK" if passed else "다중 씬 편집 시 detect_changes() 선행 필수"
        return GuardrailCheck("GR-05", passed, msg)

    @classmethod
    def run_all(cls, impact_analysis_run: bool, target_nodes: List[str], shared_nodes: List[str],
                rename_requested: bool, dry_run_completed: bool, blast_ratio: float,
                is_frozen: bool, multi_scene_edit: bool, changes_detected: bool,
                blast_threshold: float = 0.30, raise_on_violation: bool = True) -> List[GuardrailCheck]:
        checks = [
            cls.check_gr01_impact_required(impact_analysis_run, target_nodes, shared_nodes),
            cls.check_gr02_rename_dry_run(rename_requested, dry_run_completed),
            cls.check_gr03_blast_radius(blast_ratio, blast_threshold),
            cls.check_gr04_semantic_frozen(is_frozen),
            cls.check_gr05_detect_changes(multi_scene_edit, changes_detected),
        ]
        if raise_on_violation:
            for c in checks:
                if not c.passed: raise GuardrailViolation(c.rule, c.message)
        return checks
