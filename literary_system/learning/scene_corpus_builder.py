"""V385 — SceneCorpusBuilder. 원고 텍스트 → SceneFeature 배치 변환."""
from __future__ import annotations

from typing import Any, Dict, List

from literary_system.learning.privacy_guard import PrivacyGuard
from literary_system.physics.scene_feature_extractor import SceneFeature, SceneFeatureExtractor


class SceneCorpusBuilder:
    """
    원고 씬 목록 → SceneFeature 리스트.
    텍스트는 추출 즉시 폐기.
    """

    def __init__(self) -> None:
        self._extractor = SceneFeatureExtractor()
        self._guard     = PrivacyGuard()

    def build(self, scene_data_list: List[Dict[str, Any]]) -> List[SceneFeature]:
        """
        Args:
            scene_data_list: 씬 데이터 목록. 각 항목:
                {
                  'prose_report': dict,   # ReaderSurfaceScorer.report()
                  'conflict_intensity': float,
                  'scene_energy_ratio': float,
                  'motif_residue_score': float,
                  'curiosity_gradient': float,
                  'reader_uncertainty': float,
                  'reader_pull': float,
                  'reader_afterimage': float,
                }
        """
        features = []
        for data in scene_data_list:
            prose_report = data.get('prose_report', {})
            self._guard.validate(prose_report)
            feat = self._extractor.extract(
                prose_report         = prose_report,
                conflict_intensity   = data.get('conflict_intensity', 0.0),
                scene_energy_ratio   = data.get('scene_energy_ratio', 0.0),
                motif_residue_score  = data.get('motif_residue_score', 0.0),
                curiosity_gradient   = data.get('curiosity_gradient', 0.0),
                reader_uncertainty   = data.get('reader_uncertainty', 0.0),
                reader_pull          = data.get('reader_pull', 0.0),
                reader_afterimage    = data.get('reader_afterimage', 0.0),
            )
            features.append(feat)
        return features
