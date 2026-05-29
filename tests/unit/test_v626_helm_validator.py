"""V626 — HelmValidator 단위 테스트 (+30 TC)

TC-01~10: HelmValidator 기본 동작
TC-11~20: 개별 validate_ 메서드
TC-21~30: 엣지 케이스 + 통합

LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

from literary_system.ops.helm_validator import (
    CHART_API_VERSION,
    LORA_RANK_VALID,
    NAMESPACE_FORBIDDEN,
    NAMESPACE_TRAIN_ALLOWED,
    REQUIRED_CHART_FIELDS,
    REQUIRED_LORA_JOB_KEYS,
    REQUIRED_VALUES_KEYS,
    HelmValidationResult,
    HelmValidator,
    TrainPlaneChartSpec,
)

# ── 픽스처 ────────────────────────────────────────────────────────────────────

VALID_CHART: Dict[str, Any] = {
    "apiVersion": "v2",
    "name": "literary-os-train-plane",
    "description": "TrainPlane chart",
    "type": "application",
    "version": "0.1.0",
    "appVersion": "10.2.0",
}

VALID_VALUES: Dict[str, Any] = {
    "image": {"repository": "ghcr.io/test/trainer", "tag": "1.0.0", "pullPolicy": "IfNotPresent"},
    "loraJob": {
        "baseModel": "meta-llama/Llama-3.1-8B",
        "loraRank": 16,
        "loraAlpha": 32,
        "loraDropout": 0.05,
        "numEpochs": 3,
        "batchSize": 4,
        "scheduleType": "full_biweekly",
        "datasetMount": "/data/train.jsonl",
        "outputDir": "/outputs/lora",
    },
    "resources": {
        "requests": {"nvidia.com/gpu": "1", "memory": "32Gi", "cpu": "4"},
        "limits":   {"nvidia.com/gpu": "1", "memory": "64Gi", "cpu": "8"},
    },
    "costSlo": {"softUsd": 90.0, "hardUsd": 120.0, "emergencyUsd": 150.0, "monthlyTargetUsd": 96.0},
    "persistence": {"dataset": {"size": "10Gi"}, "output": {"size": "50Gi"}},
    "namespace": NAMESPACE_TRAIN_ALLOWED,
    "serviceAccount": {"create": True, "name": "literary-trainer"},
    "nodeSelector": {"workload-type": "gpu-training"},
    "tolerations": [],
    "provenance": {"historyPath": "/outputs/lora/job_history.jsonl"},
}


@pytest.fixture()
def tmp_chart_dir():
    """임시 Helm chart 디렉토리 (Chart.yaml + values.yaml + templates/ 포함)."""
    import yaml as _yaml  # noqa: F401  (선택적 의존성)
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        tmpl = p / "templates"
        tmpl.mkdir()
        (tmpl / "lora-job.yaml").write_text("# template stub")
        (tmpl / "cronjob.yaml").write_text("# template stub")
        (p / "Chart.yaml").write_text(_yaml.dump(VALID_CHART))
        (p / "values.yaml").write_text(_yaml.dump(VALID_VALUES))
        yield p


def _write_yaml(path: Path, data: Dict) -> None:
    """yaml 있으면 사용, 없으면 간단 직렬화."""
    try:
        import yaml as _yaml  # noqa: F401
        path.write_text(_yaml.dump(data))
    except ImportError:
        lines = [f"{k}: {v}" for k, v in data.items()]
        path.write_text("\n".join(lines))


# ════════════════════════════════════════════════════════════════════
# TC-01~10: HelmValidator 기본 동작
# ════════════════════════════════════════════════════════════════════

class TestHelmValidatorBasic:
    """TC-01~10: HelmValidator 기본 동작."""

    def test_tc01_import(self):
        """TC-01: 모듈 정상 import."""
        assert HelmValidator is not None
        assert HelmValidationResult is not None
        assert TrainPlaneChartSpec is not None

    def test_tc02_version(self):
        """TC-02: VERSION 속성 존재."""
        assert hasattr(HelmValidator, "VERSION")
        assert HelmValidator.VERSION == "1.0.0"

    def test_tc03_default_chart_dir(self):
        """TC-03: DEFAULT_CHART_DIR 속성."""
        assert HelmValidator.DEFAULT_CHART_DIR == "deploy/helm/train_plane"

    def test_tc04_instantiate_no_args(self):
        """TC-04: 인수 없이 인스턴스 생성."""
        v = HelmValidator()
        assert v is not None
        assert v.chart_dir == Path("deploy/helm/train_plane")

    def test_tc05_instantiate_custom_dir(self, tmp_chart_dir):
        """TC-05: 커스텀 chart_dir 설정."""
        v = HelmValidator(chart_dir=str(tmp_chart_dir))
        assert v.chart_dir == tmp_chart_dir

    def test_tc06_validate_returns_result(self, tmp_chart_dir):
        """TC-06: validate() → HelmValidationResult 반환."""
        r = HelmValidator(chart_dir=str(tmp_chart_dir)).validate()
        assert isinstance(r, HelmValidationResult)

    def test_tc07_valid_chart_passes(self, tmp_chart_dir):
        """TC-07: 정상 차트 → valid=True."""
        r = HelmValidator(chart_dir=str(tmp_chart_dir)).validate()
        assert r.valid is True
        assert len(r.errors) == 0

    def test_tc08_missing_dir_fails(self):
        """TC-08: 존재하지 않는 디렉토리 → valid=False."""
        r = HelmValidator(chart_dir="/nonexistent/path/xyz").validate()
        assert r.valid is False
        assert any("디렉토리" in e for e in r.errors)

    def test_tc09_result_has_checks(self, tmp_chart_dir):
        """TC-09: 결과에 checks 딕셔너리 포함."""
        r = HelmValidator(chart_dir=str(tmp_chart_dir)).validate()
        assert isinstance(r.checks, dict)
        assert len(r.checks) >= 9

    def test_tc10_all_checks_pass(self, tmp_chart_dir):
        """TC-10: 정상 차트 모든 체크포인트 True."""
        r = HelmValidator(chart_dir=str(tmp_chart_dir)).validate()
        for key, val in r.checks.items():
            assert val is True, f"체크포인트 실패: {key}"


# ════════════════════════════════════════════════════════════════════
# TC-11~20: 개별 validate_ 메서드
# ════════════════════════════════════════════════════════════════════

class TestHelmValidatorMethods:
    """TC-11~20: 개별 검증 메서드."""

    @pytest.fixture(autouse=True)
    def validator(self):
        self.v = HelmValidator()

    def test_tc11_validate_chart_yaml_valid(self):
        """TC-11: 유효한 Chart.yaml → (True, [])."""
        ok, errs = self.v.validate_chart_yaml(VALID_CHART)
        assert ok is True
        assert errs == []

    def test_tc12_validate_chart_yaml_missing_field(self):
        """TC-12: Chart.yaml 필수 필드 누락 → 에러."""
        bad = {k: v for k, v in VALID_CHART.items() if k != "appVersion"}
        ok, errs = self.v.validate_chart_yaml(bad)
        assert ok is False
        assert any("appVersion" in e for e in errs)

    def test_tc13_validate_chart_yaml_wrong_api_version(self):
        """TC-13: apiVersion != v2 → 에러."""
        bad = {**VALID_CHART, "apiVersion": "v1"}
        ok, errs = self.v.validate_chart_yaml(bad)
        assert ok is False
        assert any("apiVersion" in e for e in errs)

    def test_tc14_validate_values_yaml_valid(self):
        """TC-14: 유효한 values → (True, [])."""
        ok, errs = self.v.validate_values_yaml(VALID_VALUES)
        assert ok is True
        assert errs == []

    def test_tc15_validate_values_missing_key(self):
        """TC-15: values.yaml 필수 키 누락 → 에러."""
        bad = {k: v for k, v in VALID_VALUES.items() if k != "loraJob"}
        ok, errs = self.v.validate_values_yaml(bad)
        assert ok is False
        assert any("loraJob" in e for e in errs)

    def test_tc16_validate_namespace_isolation_correct(self):
        """TC-16: 올바른 네임스페이스 → (True, [])."""
        ok, errs = self.v.validate_namespace_isolation({"namespace": NAMESPACE_TRAIN_ALLOWED})
        assert ok is True

    def test_tc17_validate_namespace_isolation_forbidden(self):
        """TC-17: 금지 네임스페이스 → 에러."""
        for ns in NAMESPACE_FORBIDDEN:
            ok, errs = self.v.validate_namespace_isolation({"namespace": ns})
            assert ok is False, f"금지 네임스페이스 '{ns}' 통과됨"
            assert any("격리" in e or "불가" in e for e in errs)

    def test_tc18_validate_gpu_resources_valid(self):
        """TC-18: GPU 리소스 정상 → (True, [])."""
        ok, errs = self.v.validate_gpu_resources(VALID_VALUES)
        assert ok is True

    def test_tc19_validate_cost_slo_valid(self):
        """TC-19: SLO 논리 정상 (soft<hard<emergency) → (True, [])."""
        ok, errs = self.v.validate_cost_slo(VALID_VALUES)
        assert ok is True

    def test_tc20_validate_cost_slo_invalid_order(self):
        """TC-20: hard <= soft → 에러."""
        bad = copy.deepcopy(VALID_VALUES)
        bad["costSlo"]["hardUsd"] = 80.0  # hard < soft=90
        ok, errs = self.v.validate_cost_slo(bad)
        assert ok is False
        assert any("softUsd" in e or "hardUsd" in e for e in errs)


# ════════════════════════════════════════════════════════════════════
# TC-21~30: 엣지 케이스 + 통합
# ════════════════════════════════════════════════════════════════════

class TestHelmValidatorEdgeCases:
    """TC-21~30: 엣지 케이스 + 통합."""

    @pytest.fixture(autouse=True)
    def validator(self):
        self.v = HelmValidator()

    def test_tc21_lora_rank_valid_values(self):
        """TC-21: loraRank 허용 값들 → 에러 없음."""
        for rank in LORA_RANK_VALID:
            vals = copy.deepcopy(VALID_VALUES)
            vals["loraJob"]["loraRank"] = rank
            vals["loraJob"]["loraAlpha"] = rank * 2
            ok, errs, warns = self.v.validate_lora_hyperparams(vals)
            assert ok is True, f"rank={rank} 실패: {errs}"

    def test_tc22_lora_alpha_less_than_rank_fails(self):
        """TC-22: loraAlpha < loraRank → 에러."""
        bad = copy.deepcopy(VALID_VALUES)
        bad["loraJob"]["loraRank"] = 32
        bad["loraJob"]["loraAlpha"] = 16   # alpha < rank
        ok, errs, warns = self.v.validate_lora_hyperparams(bad)
        assert ok is False
        assert any("alpha" in e.lower() or "rank" in e.lower() for e in errs)

    def test_tc23_lora_dropout_out_of_range(self):
        """TC-23: loraDropout > 0.5 → 에러."""
        bad = copy.deepcopy(VALID_VALUES)
        bad["loraJob"]["loraDropout"] = 0.9
        ok, errs, warns = self.v.validate_lora_hyperparams(bad)
        assert ok is False
        assert any("dropout" in e.lower() for e in errs)

    def test_tc24_invalid_schedule_type(self):
        """TC-24: 허용되지 않는 scheduleType → 에러."""
        bad = copy.deepcopy(VALID_VALUES)
        bad["loraJob"]["scheduleType"] = "unknown_schedule"
        ok, errs, warns = self.v.validate_lora_hyperparams(bad)
        assert ok is False
        assert any("schedule" in e.lower() for e in errs)

    def test_tc25_missing_template_file(self, tmp_path):
        """TC-25: templates/ 파일 누락 → 에러."""
        tmpl = tmp_path / "templates"
        tmpl.mkdir()
        (tmpl / "lora-job.yaml").write_text("# stub")
        # cronjob.yaml 의도적 누락
        try:
            import yaml as _yaml
            (tmp_path / "Chart.yaml").write_text(_yaml.dump(VALID_CHART))
            (tmp_path / "values.yaml").write_text(_yaml.dump(VALID_VALUES))
        except ImportError:
            pytest.skip("PyYAML 없음")
        v = HelmValidator(chart_dir=str(tmp_path))
        ok, errs = v.validate_template_files()
        assert ok is False
        assert any("cronjob.yaml" in e for e in errs)

    def test_tc26_none_chart_returns_error(self):
        """TC-26: chart=None → 에러 반환."""
        ok, errs = self.v.validate_chart_yaml(None)
        assert ok is False
        assert len(errs) > 0

    def test_tc27_none_values_returns_error(self):
        """TC-27: values=None → 에러 반환."""
        ok, errs = self.v.validate_values_yaml(None)
        assert ok is False
        assert len(errs) > 0

    def test_tc28_gpu_missing_in_requests(self):
        """TC-28: GPU 키 누락 → 에러."""
        bad = copy.deepcopy(VALID_VALUES)
        del bad["resources"]["requests"]["nvidia.com/gpu"]
        ok, errs = self.v.validate_gpu_resources(bad)
        assert ok is False
        assert any("gpu" in e.lower() for e in errs)

    def test_tc29_service_account_warning_default_name(self):
        """TC-29: SA 이름='default' → 경고."""
        bad = copy.deepcopy(VALID_VALUES)
        bad["serviceAccount"]["name"] = "default"
        ok, warns = self.v.validate_service_account(bad)
        assert ok is True  # 에러 아님, 경고만
        assert any("default" in w for w in warns)

    def test_tc30_train_plane_spec_constants(self):
        """TC-30: TrainPlaneChartSpec 상수 검증."""
        spec = TrainPlaneChartSpec()
        assert spec.chart_name == "literary-os-train-plane"
        assert spec.api_version == CHART_API_VERSION
        assert spec.namespace == NAMESPACE_TRAIN_ALLOWED
        assert "lora-job.yaml" in spec.required_template_files
        assert "cronjob.yaml" in spec.required_template_files
