"""V385 — PhysicsCoefficientUpdater. SceneFeature 배치 → 계수 1 epoch 업데이트."""
from __future__ import annotations
from typing import List
from literary_system.physics.scene_feature_extractor import SceneFeature
from literary_system.physics.coefficient_store import PhysicsCoefficientStore


class PhysicsCoefficientUpdater:
    """
    SceneFeature 배치에서 gradient descent 1 epoch으로 계수 업데이트.
    학습률 0.01. clamp는 PhysicsCoefficientStore.update() 내부 적용.
    """
    LR = 0.01

    def __init__(self, store: PhysicsCoefficientStore) -> None:
        self._store = store

    def update_one_epoch(self, features: List[SceneFeature]) -> dict:
        """
        각 피처 필드의 평균값으로 계수를 1 step 이동.
        Returns: 업데이트된 계수 딕셔너리
        """
        if not features:
            return self._store.as_dict()

        n = len(features)
        avg = {
            'conflict_weight':       sum(f.conflict_intensity   for f in features) / n,
            'scene_energy_weight':   sum(f.scene_energy_ratio   for f in features) / n,
            'motif_weight':          sum(f.motif_residue_score  for f in features) / n,
            'curiosity_weight':      sum(f.curiosity_gradient   for f in features) / n,
            'arc_pressure_coupling': sum(f.reader_uncertainty   for f in features) / n,
            'prose_physics_bridge':  sum(f.reader_surface_score
                                         if hasattr(f, 'reader_surface_score')
                                         else f.anti_llm_score
                                         for f in features) / n,
        }
        current = self._store.as_dict()
        updates = {
            k: current[k] + self.LR * (target - current[k])
            for k, target in avg.items()
        }
        self._store.update(**updates)
        return self._store.as_dict()
