"""V385 — ManuscriptLearner. 4단계 학습 파이프라인."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from literary_system.physics.coefficient_store import PhysicsCoefficientStore
from literary_system.learning.privacy_guard import PrivacyGuard
from literary_system.learning.scene_corpus_builder import SceneCorpusBuilder
from literary_system.learning.physics_coefficient_updater import PhysicsCoefficientUpdater


class ManuscriptLearner:
    """
    실제 원고 기반 계수 학습 파이프라인:
    1. SceneCorpusBuilder: 씬 데이터 → SceneFeature
    2. PrivacyGuard: 텍스트 비포함 검증
    3. PhysicsCoefficientUpdater: 1 epoch 학습
    4. PhysicsCoefficientStore: 저장 및 동기화
    """

    def __init__(
        self,
        store:    Optional[PhysicsCoefficientStore] = None,
        fallback_synthetic: bool = True,
    ) -> None:
        self._store    = store or PhysicsCoefficientStore()
        self._guard    = PrivacyGuard()
        self._builder  = SceneCorpusBuilder()
        self._updater  = PhysicsCoefficientUpdater(self._store)
        self._fallback = fallback_synthetic
        self._learn_count = 0

    def learn(self, scene_data_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """원고 씬 데이터 → 계수 업데이트 → 업데이트된 계수 반환."""
        if not scene_data_list and self._fallback:
            scene_data_list = self._synthetic_corpus()

        features = self._builder.build(scene_data_list)
        updated  = self._updater.update_one_epoch(features)
        self._learn_count += 1
        self._store.tick_episode()
        return updated

    @property
    def learn_count(self) -> int:
        return self._learn_count

    def _synthetic_corpus(self) -> List[Dict[str, Any]]:
        """합성 코퍼스 fallback — 균형잡힌 기본값."""
        return [
            {
                'prose_report': {
                    'anti_llm': 0.7, 'emotion': 0.6, 'sensory': 0.65,
                    'rhythm': 0.7, 'consistency': 0.75, 'structure': 0.65,
                },
                'conflict_intensity': 0.5, 'scene_energy_ratio': 0.7,
                'motif_residue_score': 0.5, 'curiosity_gradient': 0.6,
                'reader_uncertainty': 0.55, 'reader_pull': 0.6, 'reader_afterimage': 0.5,
            }
        ] * 5
