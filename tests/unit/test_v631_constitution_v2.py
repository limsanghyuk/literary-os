"""
V631 — LOSConstitutionV2 단위 테스트 (SP-C.1, ADR-098)

커버리지 목표:
- entropy 헬퍼 함수
- ConstitutionWeights 분포 제약
- LOSConstitutionV2 기본 동작 (V1 상속 포함)
- Bayesian Optimisation mock (optuna stub)
- 영속화 save / load
- 엣지 케이스
"""
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest

from literary_system.constitution.los_constitution import ConstitutionWeights
from literary_system.constitution.los_constitution_v2 import (
    LOSConstitutionV2,
    OptimisationResult,
    _MIN_ENTROPY,
    _shannon_entropy,
    entropy_constraint_pass,
)


# ---------------------------------------------------------------------------
# TC-01~05: Shannon 엔트로피 헬퍼
# ---------------------------------------------------------------------------

class TestShannonEntropy:

    def test_tc01_uniform_max_entropy(self):
        """TC-01: 균등 분포 → 최대 엔트로피 log₂(5) ≈ 2.322."""
        w = [0.2, 0.2, 0.2, 0.2, 0.2]
        h = _shannon_entropy(w)
        assert abs(h - math.log2(5)) < 1e-6

    def test_tc02_degenerate_zero_entropy(self):
        """TC-02: 단일 축 집중 → 엔트로피 ≈ 0."""
        w = [1.0, 0.0, 0.0, 0.0, 0.0]
        h = _shannon_entropy(w)
        assert h < 1e-9

    def test_tc03_default_weights_entropy(self):
        """TC-03: ADR-054 기본값 (0.30/0.20/0.20/0.15/0.15) → entropy > 1.5."""
        w = ConstitutionWeights()
        h = _shannon_entropy(list(w.as_dict().values()))
        assert h >= 1.5, f"기본 가중치 엔트로피 {h:.4f} < 1.5"

    def test_tc04_entropy_increases_with_uniformity(self):
        """TC-04: 균등화할수록 엔트로피 단조 증가."""
        w_skewed = [0.80, 0.05, 0.05, 0.05, 0.05]
        w_balanced = [0.40, 0.20, 0.20, 0.10, 0.10]
        assert _shannon_entropy(w_skewed) < _shannon_entropy(w_balanced)

    def test_tc05_near_zero_weight_handled(self):
        """TC-05: 거의 0인 가중치 (1e-10) — 음의 무한대 없이 처리."""
        w = [1 - 4e-10, 1e-10, 1e-10, 1e-10, 1e-10]
        h = _shannon_entropy(w)
        assert math.isfinite(h)
        assert h >= 0.0


# ---------------------------------------------------------------------------
# TC-06~10: entropy_constraint_pass
# ---------------------------------------------------------------------------

class TestEntropyConstraintPass:

    def test_tc06_default_pass(self):
        """TC-06: 기본 ConstitutionWeights → entropy PASS."""
        w = ConstitutionWeights()
        assert entropy_constraint_pass(w) is True

    def test_tc07_extreme_fail(self):
        """TC-07: 단일 축 0.98 집중 → FAIL."""
        w = ConstitutionWeights(drse=0.98, debt=0.005, arc=0.005, tension=0.005, prose=0.005)
        assert entropy_constraint_pass(w) is False

    def test_tc08_custom_threshold(self):
        """TC-08: threshold=2.0 — 기본값은 통과 실패할 수 있음."""
        w = ConstitutionWeights()
        # 기본값 엔트로피 ≈ 2.271 → threshold=2.0 PASS
        assert entropy_constraint_pass(w, threshold=2.0) is True
        # threshold=2.35 — 5축 최대 미만이라 실패 가능
        result = entropy_constraint_pass(w, threshold=2.35)
        assert isinstance(result, bool)

    def test_tc09_balanced_weights_pass(self):
        """TC-09: 균등에 가까운 분포 → PASS."""
        w = ConstitutionWeights(drse=0.21, debt=0.20, arc=0.20, tension=0.19, prose=0.20)
        assert entropy_constraint_pass(w) is True

    def test_tc10_min_entropy_constant(self):
        """TC-10: _MIN_ENTROPY 상수값 확인."""
        assert _MIN_ENTROPY == 1.5


# ---------------------------------------------------------------------------
# TC-11~16: LOSConstitutionV2 기본 동작
# ---------------------------------------------------------------------------

class TestLOSConstitutionV2Basic:

    def test_tc11_init_default(self):
        """TC-11: 기본 생성 — V1 ADR-054 weights 상속."""
        v2 = LOSConstitutionV2()
        assert isinstance(v2.weights, ConstitutionWeights)
        assert abs(v2.weights.drse - 0.30) < 1e-6

    def test_tc12_init_custom_weights(self):
        """TC-12: 커스텀 weights 주입."""
        w = ConstitutionWeights(drse=0.25, debt=0.25, arc=0.20, tension=0.15, prose=0.15)
        v2 = LOSConstitutionV2(weights=w)
        assert abs(v2.weights.drse - 0.25) < 1e-6

    def test_tc13_entropy_ok_property(self):
        """TC-13: entropy_ok property — 기본값 True."""
        v2 = LOSConstitutionV2()
        assert v2.entropy_ok is True

    def test_tc14_current_entropy_property(self):
        """TC-14: current_entropy — 양수 float."""
        v2 = LOSConstitutionV2()
        h = v2.current_entropy
        assert isinstance(h, float)
        assert h > 0.0

    def test_tc15_score_scene_inherited(self):
        """TC-15: score_scene() V1 메서드 상속 동작."""
        v2 = LOSConstitutionV2()
        score = v2.score_scene("이 장면에서 주인공이 갈등을 겪는다.")
        assert 0.0 <= score <= 1.0

    def test_tc16_score_work_inherited(self):
        """TC-16: score_work() V1 메서드 상속 동작."""
        v2 = LOSConstitutionV2()
        scenes = ["장면1: 기막힌 전개", "장면2: 반전"]
        result = v2.score_work(scenes)
        assert hasattr(result, "mean_total")
        assert 0.0 <= result.mean_total <= 1.0


# ---------------------------------------------------------------------------
# TC-17~22: optimise_weights (optuna mock)
# ---------------------------------------------------------------------------

class TestOptimiseWeightsMocked:
    """Optuna를 mock하여 optuna 미설치 환경에서도 로직 검증."""

    def _make_mock_optuna(self, best_params: dict, best_value: float):
        """Optuna study/trial mock 생성 헬퍼."""
        mock_optuna = MagicMock()

        mock_trial = MagicMock()
        mock_trial.state.name = "COMPLETE"
        mock_trial.params = best_params
        mock_trial.value = best_value

        mock_study = MagicMock()
        mock_study.trials = [mock_trial]
        mock_study.best_trial = mock_trial

        mock_optuna.samplers.TPESampler.return_value = MagicMock()
        mock_optuna.create_study.return_value = mock_study
        mock_optuna.logging = MagicMock()
        mock_optuna.logging.WARNING = 30

        return mock_optuna

    def test_tc17_optimise_returns_result(self):
        """TC-17: mock optuna — OptimisationResult 반환 확인."""
        best_params = {
            "drse": 0.30, "debt": 0.20, "arc": 0.20,
            "tension": 0.15, "prose": 0.15,
        }
        mock_optuna = self._make_mock_optuna(best_params, 0.001)

        with patch.dict("sys.modules", {"optuna": mock_optuna,
                                         "optuna.samplers": mock_optuna.samplers,
                                         "optuna.exceptions": MagicMock()}):
            v2 = LOSConstitutionV2()
            samples: List[Tuple[str, float]] = [
                ("장면 텍스트 샘플 1 — 주인공 갈등", 0.75),
                ("장면 텍스트 샘플 2 — 반전", 0.80),
            ]
            result = v2.optimise_weights(samples, n_trials=5)

        assert isinstance(result, OptimisationResult)

    def test_tc18_empty_samples_raises(self):
        """TC-18: 빈 samples → ValueError."""
        v2 = LOSConstitutionV2()
        with pytest.raises(ValueError, match="samples"):
            v2.optimise_weights([])

    def test_tc19_optimise_import_error(self):
        """TC-19: optuna 미설치 → ImportError."""
        v2 = LOSConstitutionV2()
        with patch.dict("sys.modules", {"optuna": None}):
            with pytest.raises(ImportError):
                v2.optimise_weights([("텍스트", 0.7)])

    def test_tc20_history_appended(self):
        """TC-20: optimise_weights 호출 후 history 길이 증가."""
        best_params = {
            "drse": 0.28, "debt": 0.22, "arc": 0.20,
            "tension": 0.16, "prose": 0.14,
        }
        mock_optuna = self._make_mock_optuna(best_params, 0.002)

        with patch.dict("sys.modules", {"optuna": mock_optuna,
                                         "optuna.samplers": mock_optuna.samplers,
                                         "optuna.exceptions": MagicMock()}):
            v2 = LOSConstitutionV2()
            assert len(v2.optimisation_history) == 0
            samples = [("샘플 텍스트", 0.72)]
            v2.optimise_weights(samples, n_trials=3)
            assert len(v2.optimisation_history) == 1

    def test_tc21_optimise_no_completed_trials(self):
        """TC-21: 모든 trial pruned → converged=False, 기본값 유지."""
        mock_optuna = MagicMock()
        mock_study = MagicMock()
        mock_study.trials = []  # 완료된 trial 없음
        mock_optuna.samplers.TPESampler.return_value = MagicMock()
        mock_optuna.create_study.return_value = mock_study
        mock_optuna.logging = MagicMock()
        mock_optuna.logging.WARNING = 30

        with patch.dict("sys.modules", {"optuna": mock_optuna,
                                         "optuna.samplers": mock_optuna.samplers,
                                         "optuna.exceptions": MagicMock()}):
            v2 = LOSConstitutionV2()
            original_drse = v2.weights.drse
            result = v2.optimise_weights([("텍스트", 0.7)], n_trials=3)

        assert result.converged is False
        assert result.best_mse == float("inf")
        # weights 변경 없음
        assert abs(v2.weights.drse - original_drse) < 1e-9

    def test_tc22_optimisation_result_to_dict(self):
        """TC-22: OptimisationResult.to_dict() 구조 검증."""
        w = ConstitutionWeights()
        r = OptimisationResult(
            best_weights=w,
            best_mse=0.005,
            entropy=2.2,
            n_trials=100,
            n_pruned=3,
            converged=True,
        )
        d = r.to_dict()
        assert "best_weights" in d
        assert "best_mse" in d
        assert "entropy" in d
        assert "converged" in d
        assert d["converged"] is True
        assert abs(d["best_mse"] - 0.005) < 1e-9


# ---------------------------------------------------------------------------
# TC-23~28: 영속화 save / load
# ---------------------------------------------------------------------------

class TestSaveLoad:

    def test_tc23_save_creates_file(self):
        """TC-23: save() → JSON 파일 생성."""
        v2 = LOSConstitutionV2()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            v2.save(path)
            assert path.exists()

    def test_tc24_save_json_structure(self):
        """TC-24: 저장된 JSON 구조 검증."""
        v2 = LOSConstitutionV2()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            v2.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
        assert data["version"] == "2.0"
        assert data["adr"] == "ADR-098"
        assert "weights" in data
        assert "entropy_threshold" in data
        assert "entropy_ok" in data

    def test_tc25_load_restores_weights(self):
        """TC-25: load() → 동일 weights 복원."""
        w = ConstitutionWeights(drse=0.25, debt=0.25, arc=0.20, tension=0.15, prose=0.15)
        v2 = LOSConstitutionV2(weights=w)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            v2.save(path)
            v2_loaded = LOSConstitutionV2.load(path)
        assert abs(v2_loaded.weights.drse - 0.25) < 1e-6
        assert abs(v2_loaded.weights.debt - 0.25) < 1e-6

    def test_tc26_load_preserves_entropy_threshold(self):
        """TC-26: load() → entropy_threshold 복원."""
        v2 = LOSConstitutionV2(entropy_threshold=1.8)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            v2.save(path)
            v2_loaded = LOSConstitutionV2.load(path)
        assert abs(v2_loaded._entropy_threshold - 1.8) < 1e-9

    def test_tc27_roundtrip_score_consistency(self):
        """TC-27: save → load 후 score_scene() 동일 결과."""
        v2 = LOSConstitutionV2()
        text = "주인공이 비밀을 알게 되는 충격적인 장면."
        original_score = v2.score_scene(text)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            v2.save(path)
            v2_loaded = LOSConstitutionV2.load(path)
        loaded_score = v2_loaded.score_scene(text)
        assert abs(original_score - loaded_score) < 1e-9

    def test_tc28_loaded_entropy_ok(self):
        """TC-28: load() → entropy_ok 속성 정상 동작."""
        v2 = LOSConstitutionV2()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "weights.json"
            v2.save(path)
            v2_loaded = LOSConstitutionV2.load(path)
        assert isinstance(v2_loaded.entropy_ok, bool)


# ---------------------------------------------------------------------------
# TC-29~33: 엣지 케이스 / 통합 검증
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_tc29_custom_entropy_threshold_init(self):
        """TC-29: 사용자 지정 threshold 적용."""
        v2 = LOSConstitutionV2(entropy_threshold=2.0)
        assert abs(v2._entropy_threshold - 2.0) < 1e-9
        # 기본값 2.271 > 2.0 → PASS
        assert v2.entropy_ok is True

    def test_tc30_optimisation_history_readonly(self):
        """TC-30: optimisation_history 반환값 수정이 내부 상태에 영향 없음."""
        v2 = LOSConstitutionV2()
        hist = v2.optimisation_history
        assert isinstance(hist, list)
        # 반환된 리스트를 수정해도 내부 상태 변경 없음
        hist.append(None)  # type: ignore
        assert len(v2.optimisation_history) == 0

    def test_tc31_v2_inherits_rlhf_reward(self):
        """TC-31: V1 rlhf_reward() 상속 동작."""
        v2 = LOSConstitutionV2()
        reward = v2.rlhf_reward("생성된 텍스트", "원본 텍스트")
        assert -1.0 <= reward <= 1.0

    def test_tc32_entropy_constraint_pass_returns_bool(self):
        """TC-32: entropy_constraint_pass() 반환 타입 bool."""
        w = ConstitutionWeights()
        result = entropy_constraint_pass(w)
        assert type(result) is bool

    def test_tc33_shannon_entropy_known_values(self):
        """TC-33: 알려진 분포 엔트로피 값 검증."""
        # 2개 균등 분포: H = log₂(2) = 1.0
        w_two = [0.5, 0.5, 0.0, 0.0, 0.0]
        h_two = _shannon_entropy(w_two)
        assert abs(h_two - 1.0) < 1e-6

        # 4개 균등 분포: H = log₂(4) = 2.0
        w_four = [0.25, 0.25, 0.25, 0.25, 0.0]
        h_four = _shannon_entropy(w_four)
        assert abs(h_four - 2.0) < 1e-6
