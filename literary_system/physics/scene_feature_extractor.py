"""
V383 — SceneFeatureExtractor
13필드 SceneFeature 추출기. 텍스트 비저장 원칙 강제.
(V385 ManuscriptLearning을 위한 피처 추출 인프라)
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SceneFeature:
    """13필드 씬 피처. 텍스트 미포함."""
    # Group 1: prose 품질 (6)
    anti_llm_score:      float = 0.0
    emotion_score:       float = 0.0
    sensory_score:       float = 0.0
    rhythm_score:        float = 0.0
    consistency_score:   float = 0.0
    structure_score:     float = 0.0
    # Group 2: physics 물리량 (4)
    conflict_intensity:  float = 0.0
    scene_energy_ratio:  float = 0.0
    motif_residue_score: float = 0.0
    curiosity_gradient:  float = 0.0
    # Group 3: trajectory 독자지표 (3)
    reader_uncertainty:  float = 0.0
    reader_pull:         float = 0.0
    reader_afterimage:   float = 0.0

    def as_vector(self) -> list:
        return [
            self.anti_llm_score, self.emotion_score, self.sensory_score,
            self.rhythm_score, self.consistency_score, self.structure_score,
            self.conflict_intensity, self.scene_energy_ratio,
            self.motif_residue_score, self.curiosity_gradient,
            self.reader_uncertainty, self.reader_pull, self.reader_afterimage,
        ]

    def __len__(self) -> int:
        return 13


class PrivacyGuardViolation(Exception):
    """SceneFeature에 텍스트 데이터가 포함된 경우."""


class SceneFeatureExtractor:
    """
    prose 품질 점수 + physics 물리량 + trajectory 지표를 조합하여
    SceneFeature 13필드를 구성한다.
    원고 텍스트는 이 클래스 내부에 저장되지 않는다.
    """

    def extract(
        self,
        # prose 품질 (ReaderSurfaceScorer.report() 결과)
        prose_report: dict,
        # physics 물리량 (PhysicsRunResult에서)
        conflict_intensity:  float = 0.0,
        scene_energy_ratio:  float = 0.0,
        motif_residue_score: float = 0.0,
        curiosity_gradient:  float = 0.0,
        # trajectory 독자지표 (ReaderSimulator에서)
        reader_uncertainty:  float = 0.0,
        reader_pull:         float = 0.0,
        reader_afterimage:   float = 0.0,
    ) -> SceneFeature:
        """
        Args:
            prose_report: ReaderSurfaceScorer.report() → dict with keys:
                anti_llm, emotion, sensory, rhythm, consistency, structure
        """
        self._guard_no_text(prose_report)
        return SceneFeature(
            anti_llm_score      = float(prose_report.get('anti_llm',    0.0)),
            emotion_score       = float(prose_report.get('emotion',     0.0)),
            sensory_score       = float(prose_report.get('sensory',     0.0)),
            rhythm_score        = float(prose_report.get('rhythm',      0.0)),
            consistency_score   = float(prose_report.get('consistency', 0.0)),
            structure_score     = float(prose_report.get('structure',   0.0)),
            conflict_intensity  = conflict_intensity,
            scene_energy_ratio  = scene_energy_ratio,
            motif_residue_score = motif_residue_score,
            curiosity_gradient  = curiosity_gradient,
            reader_uncertainty  = reader_uncertainty,
            reader_pull         = reader_pull,
            reader_afterimage   = reader_afterimage,
        )

    @staticmethod
    def _guard_no_text(d: dict) -> None:
        """dict 값 중 길이 > 100인 문자열이 있으면 PrivacyGuardViolation."""
        for k, v in d.items():
            if isinstance(v, str) and len(v) > 100:
                raise PrivacyGuardViolation(
                    f"Field '{k}' contains text data (len={len(v)}). "
                    "Only numeric scores are allowed in SceneFeature."
                )
