"""
V602 — 단위 테스트: RLHFDatasetBuilder (8 TC)

TC-A1~A3: 기본 build() 동작
TC-B1~B2: 유효성 검사 (ValueError)
TC-C1~C3: build_dual() + load() + split 비율
"""
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

from literary_system.rlhf.rlhf_dataset_builder import (
    BuildResult,
    DatasetEntry,
    DatasetStats,
    RLHFDatasetBuilder,
)
from literary_system.rlhf.reward_model import REWARD_THRESHOLD

# ---------------------------------------------------------------------------
# 픽스처
# ---------------------------------------------------------------------------

DRAMA_SCENES = [
    (
        "주인공이 빗속을 걷다 멈춰 서며 하늘을 올려다보았다. "
        "그의 눈에는 오랜 슬픔과 새로운 결심이 뒤섞여 있었다. "
        "오늘이 지나면 모든 것이 달라질 것이라는 예감이 들었다. "
        "그는 천천히 문 앞에 섰다. 그녀가 바라보고 있었다. "
        "두 사람 사이의 침묵이 긴장감을 고조시켰다."
    ),
    (
        "그는 마침내 각오를 다졌다. 이 선택이 모든 것을 바꿀 것이다. "
        "캐릭터의 아크가 정점에 달하는 순간이었다. "
        "갈등이 충돌하며 반전이 시작되었다. "
        "두 사람의 대치가 절정으로 치달았다."
    ),
    (
        "드라마틱한 결말을 향한 각오. 새로운 결심과 변화의 예감. "
        "마침내 드디어 선택의 순간이 왔다. 갈등이 해소되는 순간. "
        "감동적인 씬이 펼쳐졌다. 주인공은 눈물을 흘렸다."
    ),
]

SHORT_SCENE = "짧은 씬."  # reward < threshold (passed=False)


# ---------------------------------------------------------------------------
# TC-A: 기본 build() 동작
# ---------------------------------------------------------------------------


class TestBuildBasic:
    """TC-A1~A3: 기본 build() 동작."""

    def test_a1_build_returns_build_result(self, tmp_path: Path) -> None:
        """TC-A1: build()가 BuildResult를 반환해야 한다."""
        builder = RLHFDatasetBuilder()
        out = tmp_path / "out.jsonl"
        result = builder.build(DRAMA_SCENES, out, filter_passed=False)

        assert isinstance(result, BuildResult)
        assert result.output_path == out
        assert result.entry_count == len(DRAMA_SCENES)
        assert result.model_target == "both"
        assert result.reward_threshold == REWARD_THRESHOLD

    def test_a2_filter_passed_excludes_failed_scenes(self, tmp_path: Path) -> None:
        """TC-A2: filter_passed=True 이면 passed=False 씬이 제외되어야 한다."""
        scenes = DRAMA_SCENES + [SHORT_SCENE]
        builder = RLHFDatasetBuilder()
        out = tmp_path / "filtered.jsonl"
        result = builder.build(scenes, out, filter_passed=True)

        # 모든 항목의 passed=True여야 함
        entries = builder.load(out)
        assert all(e.passed for e in entries), "filter_passed=True 인데 passed=False 항목 존재"
        assert result.entry_count == len(entries)

    def test_a3_jsonl_has_correct_fields(self, tmp_path: Path) -> None:
        """TC-A3: JSONL 파일 각 행이 DatasetEntry 필드를 모두 포함해야 한다."""
        builder = RLHFDatasetBuilder()
        out = tmp_path / "fields.jsonl"
        builder.build(DRAMA_SCENES[:1], out, filter_passed=False)

        with out.open("r", encoding="utf-8") as fh:
            row = json.loads(fh.readline())

        required_fields = {
            "entry_id", "scene", "reward", "passed",
            "axis_rewards", "model_target", "split",
        }
        assert required_fields.issubset(row.keys()), (
            f"누락 필드: {required_fields - row.keys()}"
        )
        assert 0.0 <= row["reward"] <= 1.0
        assert row["model_target"] == "both"
        assert row["split"] in ("train", "val", "test")
        assert len(row["axis_rewards"]) == 5


# ---------------------------------------------------------------------------
# TC-B: 유효성 검사
# ---------------------------------------------------------------------------


class TestValidation:
    """TC-B1~B2: ValueError 발생 조건."""

    def test_b1_invalid_model_target_raises(self) -> None:
        """TC-B1: 지원되지 않는 model_target에서 ValueError가 발생해야 한다."""
        with pytest.raises(ValueError, match="model_target"):
            RLHFDatasetBuilder(model_target="32B")

    def test_b2_invalid_split_ratio_raises(self) -> None:
        """TC-B2: split_ratio 합이 1.0이 아니면 ValueError가 발생해야 한다."""
        with pytest.raises(ValueError, match="split_ratio"):
            RLHFDatasetBuilder(split_ratio=(0.70, 0.20, 0.20))  # 합 = 1.10


# ---------------------------------------------------------------------------
# TC-C: build_dual() + load() + split 비율
# ---------------------------------------------------------------------------


class TestDualAndLoad:
    """TC-C1~C3: 듀얼 빌드, 파일 재로드, 분할 비율 검증."""

    def test_c1_build_dual_creates_two_files(self, tmp_path: Path) -> None:
        """TC-C1: build_dual()이 8B/3B 두 파일을 생성해야 한다."""
        builder = RLHFDatasetBuilder()
        results = builder.build_dual(DRAMA_SCENES, tmp_path, filter_passed=False)

        assert set(results.keys()) == {"8B", "3B"}
        for target, res in results.items():
            assert res.output_path.exists(), f"{target} 파일 미생성"
            assert res.model_target == target
            # 두 파일의 entry_count는 동일해야 함
        assert results["8B"].entry_count == results["3B"].entry_count

    def test_c2_load_roundtrip(self, tmp_path: Path) -> None:
        """TC-C2: build() 후 load()로 재로드 시 동일한 항목이어야 한다."""
        builder = RLHFDatasetBuilder()
        out = tmp_path / "rt.jsonl"
        build_result = builder.build(DRAMA_SCENES, out, filter_passed=False)

        loaded = builder.load(out)
        assert len(loaded) == build_result.entry_count
        for entry in loaded:
            assert isinstance(entry, DatasetEntry)
            assert 0.0 <= entry.reward <= 1.0
            assert entry.split in ("train", "val", "test")

    def test_c3_split_ratio_respected(self, tmp_path: Path) -> None:
        """TC-C3: train/val/test 분할 비율이 근사 달성되어야 한다."""
        # 충분히 많은 씬을 생성
        many_scenes = DRAMA_SCENES * 10  # 30 씬
        builder = RLHFDatasetBuilder(split_ratio=(0.80, 0.10, 0.10))
        out = tmp_path / "split.jsonl"
        builder.build(many_scenes, out, filter_passed=False)

        loaded = builder.load(out)
        total = len(loaded)
        train_n = sum(1 for e in loaded if e.split == "train")
        val_n = sum(1 for e in loaded if e.split == "val")
        test_n = sum(1 for e in loaded if e.split == "test")

        assert train_n + val_n + test_n == total, "분할 합이 total과 불일치"
        # train 비율이 70%~90% 사이여야 함 (floor() 사용으로 약간의 편차 허용)
        train_ratio = train_n / total
        assert 0.70 <= train_ratio <= 0.90, f"train 비율 {train_ratio:.2f} 범위 이탈"

    def test_summary_stats(self, tmp_path: Path) -> None:
        """TC-추가: summary()가 올바른 통계를 반환해야 한다."""
        builder = RLHFDatasetBuilder()
        out = tmp_path / "summary.jsonl"
        builder.build(DRAMA_SCENES + [SHORT_SCENE], out, filter_passed=False)

        stats = builder.summary(out)
        assert stats["total"] == len(DRAMA_SCENES) + 1
        assert 0 <= stats["pass_count"] <= stats["total"]
        assert 0.0 <= stats["pass_rate"] <= 1.0
        assert 0.0 <= stats["mean_reward"] <= 1.0
        assert stats["train"] + stats["val"] + stats["test"] == stats["total"]
