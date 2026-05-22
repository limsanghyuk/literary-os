"""
literary_system/rlhf/rlhf_dataset_builder.py

V602 — RLHFDatasetBuilder v1.0
SP-B.2 RLHF 루프 2단계: (씬, 보상) 쌍 JSONL 데이터셋 빌더

LLM-0 원칙: 외부 LLM API 호출 없음.
"""
from __future__ import annotations

import json
import math
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from literary_system.rlhf.reward_model import REWARD_THRESHOLD, RewardModel, RewardResult

__all__ = [
    "RLHFDatasetBuilder",
    "DatasetEntry",
    "RLHFDatasetStats",
    "BuildResult",
]

# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------


@dataclass
class DatasetEntry:
    """JSONL 한 줄에 해당하는 (씬, 보상) 쌍."""

    entry_id: str
    scene: str
    reward: float
    passed: bool
    axis_rewards: Dict[str, float]  # {axis: raw_score}
    model_target: str               # "8B" | "3B" | "both"
    split: str                      # "train" | "val" | "test"


@dataclass
class RLHFDatasetStats:
    """데이터셋 통계."""

    total: int = 0
    pass_count: int = 0
    fail_count: int = 0
    mean_reward: float = 0.0
    min_reward: float = 1.0
    max_reward: float = 0.0
    train_count: int = 0
    val_count: int = 0
    test_count: int = 0


@dataclass
class BuildResult:
    """build() / build_dual() 결과."""

    output_path: Path
    stats: RLHFDatasetStats
    entry_count: int
    model_target: str
    reward_threshold: float


# ---------------------------------------------------------------------------
# 빌더 본체
# ---------------------------------------------------------------------------


class RLHFDatasetBuilder:
    """
    (씬, 보상) 쌍 JSONL 데이터셋 빌더.

    주요 기능:
    - RewardModel로 씬 보상 계산
    - 품질 필터링 (reward >= threshold)
    - 8B / 3B 듀얼 dataset 지원
    - 결정론적 train / val / test 분할
    - JSONL 저장 + 재로드
    """

    SUPPORTED_TARGETS: Tuple[str, ...] = ("8B", "3B", "both")
    DEFAULT_SPLIT_RATIO: Tuple[float, float, float] = (0.80, 0.10, 0.10)

    def __init__(
        self,
        reward_model: Optional[RewardModel] = None,
        reward_threshold: float = REWARD_THRESHOLD,
        split_ratio: Tuple[float, float, float] = DEFAULT_SPLIT_RATIO,
        model_target: str = "both",
    ) -> None:
        if model_target not in self.SUPPORTED_TARGETS:
            raise ValueError(
                f"model_target='{model_target}'은 지원되지 않습니다. "
                f"선택 가능: {self.SUPPORTED_TARGETS}"
            )
        if abs(sum(split_ratio) - 1.0) > 1e-6:
            raise ValueError(
                f"split_ratio 합이 1.0이어야 합니다. 현재 합={sum(split_ratio):.6f}"
            )

        self._rm: RewardModel = reward_model if reward_model is not None else RewardModel()
        self._threshold: float = reward_threshold
        self._split_ratio: Tuple[float, float, float] = split_ratio
        self._model_target: str = model_target

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def build(
        self,
        scenes: Sequence[str],
        output_path: "Path | str",
        *,
        filter_passed: bool = True,
    ) -> BuildResult:
        """
        씬 목록을 받아 JSONL 파일로 저장한다.

        Args:
            scenes: 씬 텍스트 목록.
            output_path: 출력 경로 (.jsonl).
            filter_passed: True 이면 passed=True 인 씬만 포함.

        Returns:
            BuildResult (output_path, stats, entry_count, model_target, threshold).
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1단계: 보상 계산
        results: List[RewardResult] = self._rm.compute_batch(list(scenes))

        # 2단계: 필터링
        pairs: List[Tuple[str, RewardResult]] = [
            (s, r) for s, r in zip(scenes, results)
            if (not filter_passed) or r.passed
        ]

        # 3단계: DatasetEntry 생성 + JSONL 직렬화
        entries = self._make_entries(pairs)

        with output_path.open("w", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

        stats = self._compute_stats(entries)

        return BuildResult(
            output_path=output_path,
            stats=stats,
            entry_count=len(entries),
            model_target=self._model_target,
            reward_threshold=self._threshold,
        )

    def build_dual(
        self,
        scenes: Sequence[str],
        output_dir: "Path | str",
        *,
        filter_passed: bool = True,
    ) -> Dict[str, BuildResult]:
        """
        8B / 3B 듀얼 데이터셋 생성.

        동일한 씬/보상 데이터를 model_target별 JSONL에 분리 저장한다.

        Returns:
            {"8B": BuildResult, "3B": BuildResult}
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        dual_results: Dict[str, BuildResult] = {}
        for target in ("8B", "3B"):
            sub = RLHFDatasetBuilder(
                reward_model=self._rm,
                reward_threshold=self._threshold,
                split_ratio=self._split_ratio,
                model_target=target,
            )
            path = output_dir / f"rlhf_dataset_{target}.jsonl"
            dual_results[target] = sub.build(scenes, path, filter_passed=filter_passed)

        return dual_results

    def load(self, path: "Path | str") -> List[DatasetEntry]:
        """JSONL 파일을 DatasetEntry 목록으로 로드한다."""
        path = Path(path)
        entries: List[DatasetEntry] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entries.append(DatasetEntry(**data))
        return entries

    def summary(self, path: "Path | str") -> Dict[str, object]:
        """저장된 JSONL의 요약 통계를 반환한다."""
        entries = self.load(path)
        stats = self._compute_stats(entries)
        return {
            "total": stats.total,
            "pass_count": stats.pass_count,
            "pass_rate": round(stats.pass_count / max(1, stats.total), 4),
            "mean_reward": stats.mean_reward,
            "min_reward": stats.min_reward,
            "max_reward": stats.max_reward,
            "train": stats.train_count,
            "val": stats.val_count,
            "test": stats.test_count,
        }

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _assign_split(self, index: int, total: int) -> str:
        """인덱스 기반 결정론적 train / val / test 분할."""
        if total == 0:
            return "train"
        train_n = math.floor(total * self._split_ratio[0])
        val_n = math.floor(total * self._split_ratio[1])
        if index < train_n:
            return "train"
        if index < train_n + val_n:
            return "val"
        return "test"

    def _make_entries(
        self, pairs: List[Tuple[str, RewardResult]]
    ) -> List[DatasetEntry]:
        """(scene, RewardResult) 쌍을 DatasetEntry 목록으로 변환."""
        total = len(pairs)
        entries: List[DatasetEntry] = []
        for idx, (scene, result) in enumerate(pairs):
            axis_dict = {
                ar.axis: round(ar.raw_score, 4)
                for ar in result.axis_rewards
            }
            entry = DatasetEntry(
                entry_id=str(uuid.uuid4()),
                scene=scene,
                reward=round(result.reward, 6),
                passed=result.passed,
                axis_rewards=axis_dict,
                model_target=self._model_target,
                split=self._assign_split(idx, total),
            )
            entries.append(entry)
        return entries

    def _compute_stats(self, entries: List[DatasetEntry]) -> RLHFDatasetStats:
        """DatasetEntry 목록에서 RLHFDatasetStats를 계산한다."""
        if not entries:
            return RLHFDatasetStats()
        rewards = [e.reward for e in entries]
        return RLHFDatasetStats(
            total=len(entries),
            pass_count=sum(1 for e in entries if e.passed),
            fail_count=sum(1 for e in entries if not e.passed),
            mean_reward=round(sum(rewards) / len(rewards), 4),
            min_reward=round(min(rewards), 4),
            max_reward=round(max(rewards), 4),
            train_count=sum(1 for e in entries if e.split == "train"),
            val_count=sum(1 for e in entries if e.split == "val"),
            test_count=sum(1 for e in entries if e.split == "test"),
        )
