"""DatasetSplitter — LoRASample 8:1:1 train/val/test 분할기.

ADR-056: seed=42 고정, stratified 옵션 지원.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

from literary_system.finetune.lora_dataset_builder import LoRASample

DEFAULT_TRAIN_RATIO: float = 0.8
DEFAULT_VAL_RATIO: float = 0.1
DEFAULT_TEST_RATIO: float = 0.1
DEFAULT_SEED: int = 42


@dataclass
class LoRADatasetSplit:
    """LoRA 분할 결과 컨테이너."""

    train: List[LoRASample]
    val: List[LoRASample]
    test: List[LoRASample]

    @property
    def total(self) -> int:
        return len(self.train) + len(self.val) + len(self.test)

    @property
    def ratios(self) -> Dict[str, float]:
        t = self.total or 1
        return {
            "train": len(self.train) / t,
            "val": len(self.val) / t,
            "test": len(self.test) / t,
        }

    def __repr__(self) -> str:
        r = self.ratios
        return (
            f"LoRADatasetSplit("
            f"train={len(self.train)} ({r['train']:.1%}), "
            f"val={len(self.val)} ({r['val']:.1%}), "
            f"test={len(self.test)} ({r['test']:.1%}))"
        )


class DatasetSplitter:
    """LoRASample 리스트를 train/val/test로 분할.

    Usage:
        splitter = DatasetSplitter()
        split = splitter.split(samples)
        # LoRADatasetSplit(train=800 (80.0%), val=100 (10.0%), test=100 (10.0%))
    """

    def __init__(
        self,
        train_ratio: float = DEFAULT_TRAIN_RATIO,
        val_ratio: float = DEFAULT_VAL_RATIO,
        test_ratio: float = DEFAULT_TEST_RATIO,
        seed: int = DEFAULT_SEED,
    ) -> None:
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-9, (
            "Ratios must sum to 1.0"
        )
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def split(
        self,
        samples: List[LoRASample],
        stratified: bool = False,
        stratify_key: str = "source_type",
    ) -> LoRADatasetSplit:
        """샘플을 분할. stratified=True 시 source_type 별 균등 분배."""
        if not samples:
            return LoRADatasetSplit(train=[], val=[], test=[])

        if stratified:
            return self._stratified_split(samples, stratify_key)
        return self._random_split(samples)

    def _random_split(self, samples: List[LoRASample]) -> LoRADatasetSplit:
        rng = random.Random(self.seed)
        shuffled = list(samples)
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_train = int(n * self.train_ratio)
        n_val = int(n * self.val_ratio)
        return LoRADatasetSplit(
            train=shuffled[:n_train],
            val=shuffled[n_train : n_train + n_val],
            test=shuffled[n_train + n_val :],
        )

    def _stratified_split(
        self, samples: List[LoRASample], key: str
    ) -> LoRADatasetSplit:
        groups: Dict[str, List[LoRASample]] = {}
        for s in samples:
            k = getattr(s, key, "unknown")
            groups.setdefault(k, []).append(s)

        trains, vals, tests = [], [], []
        for group in groups.values():
            sp = self._random_split(group)
            trains.extend(sp.train)
            vals.extend(sp.val)
            tests.extend(sp.test)
        return LoRADatasetSplit(train=trains, val=vals, test=tests)
