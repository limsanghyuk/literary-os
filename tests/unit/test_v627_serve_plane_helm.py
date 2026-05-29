"""tests/unit/test_v627_serve_plane_helm.py

V627 ServePlane Helm 검증기 테스트 (50 TC)
- TC-01~10: TestServePlaneValidatorBasic
- TC-11~20: TestServePlaneValidatorMethods
- TC-21~30: TestLLM1AndNamespaceIsolation
- TC-31~40: TestCPUResourcesAndHPA
- TC-41~50: TestEdgeCasesAndIntegration

설계 원칙:
  LLM-1: PROMOTED 단계 LoRA 모델만 서빙 허용 (ADR-058)
  LLM-0: corpus/constitution/finetune 외부 LLM 호출 금지 (ADR-034)
  Namespace isolation: literary-serve 전용, literary-train 금지 (ADR-057 §5)
  CPU-only: ServePlane에 GPU 요청 금지
"""

from __future__ import annotations

import sys
import os
import copy
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from literary_system.serving.serve_plane_validator import (
    ServePlaneChartSpec,
    ServePlaneValidationResult,
    ServePlaneValidator,
    ServePlaneValuesSpec,
)


# ─────────────────────────────────────────────
# 헬퍼 — 실제 values.yaml 스펙 완전 매칭
# ─────────────────────────────────────────────
def _valid_values() -> dict:
    """실제 deploy/helm/serve_plane/values.yaml과 동일한 구조."""
    return {
        "namespace": "literary-serve",
        "replicaCount": 2,
        "image": {
            "repository": "ghcr.io/limsanghyuk/literary-os-server",
            "tag": "10.31.0",
            "pullPolicy": "IfNotPresent",
        },
        "model": {
            "name": "literary-os-serve",
            "baseModel": "meta-llama/Llama-3.1-8B",
            "modelMount": "/models/lora",
            "requirePromoted": True,
            "maxSeqLen": 2048,
            "batchSize": 8,
        },
        "resources": {
            "requests": {"cpu": "2", "memory": "8Gi"},
            "limits": {"cpu": "4", "memory": "16Gi"},
        },
        "autoscaling": {
            "enabled": True,
            "minReplicas": 2,
            "maxReplicas": 8,
            "targetCPUUtilizationPercentage": 70,
            "targetMemoryUtilizationPercentage": 80,
        },
        "serving": {
            "port": 8080,
            "workers": 4,
            "timeoutSec": 30,
            "maxConcurrent": 100,
            "logLevel": "INFO",
        },
        "healthCheck": {
            "enabled": True,
            "livenessPath": "/health/live",
            "readinessPath": "/health/ready",
            "initialDelaySeconds": 30,
            "periodSeconds": 10,
            "failureThreshold": 3,
        },
        "service": {
            "type": "ClusterIP",
            "port": 80,
            "targetPort": 8080,
        },
        "persistence": {
            "models": {
                "storageClass": "standard",
                "size": "20Gi",
                "accessMode": "ReadOnlyMany",
            }
        },
        "serviceAccount": {
            "create": True,
            "name": "literary-server",
        },
    }


def _valid_chart() -> dict:
    """실제 deploy/helm/serve_plane/Chart.yaml 구조."""
    return {
        "apiVersion": "v2",
        "name": "literary-os-serve-plane",
        "description": "Literary OS ServePlane Helm Chart — CPU inference only",
        "type": "application",
        "version": "0.1.0",
        "appVersion": "10.31.0",
    }


# ─────────────────────────────────────────────
# TC-01~10: TestServePlaneValidatorBasic
# ─────────────────────────────────────────────
class TestServePlaneValidatorBasic(unittest.TestCase):
    """ServePlaneValidator 기본 동작 10건."""

    def test_tc01_default_chart_dir(self):
        """TC-01: DEFAULT_CHART_DIR는 deploy/helm/serve_plane."""
        self.assertEqual(ServePlaneValidator.DEFAULT_CHART_DIR, "deploy/helm/serve_plane")

    def test_tc02_version_attribute(self):
        """TC-02: VERSION 속성 존재."""
        v = ServePlaneValidator()
        self.assertTrue(hasattr(v, "VERSION"))
        self.assertIsInstance(v.VERSION, str)

    def test_tc03_custom_chart_dir_stored(self):
        """TC-03: 사용자 정의 chart_dir 인수가 chart_dir 속성에 저장."""
        v = ServePlaneValidator(chart_dir="/custom/path")
        # chart_dir 또는 _chart_dir 속성에 저장될 수 있음
        stored = getattr(v, "chart_dir", None) or getattr(v, "_chart_dir", None)
        self.assertIsNotNone(stored)

    def test_tc04_validate_returns_result(self):
        """TC-04: validate()가 ServePlaneValidationResult 반환."""
        v = ServePlaneValidator()
        result = v.validate()
        self.assertIsInstance(result, ServePlaneValidationResult)

    def test_tc05_valid_chart_passes(self):
        """TC-05: 정상 ServePlane chart 디렉터리 → valid=True."""
        v = ServePlaneValidator()
        result = v.validate()
        self.assertTrue(result.valid, f"Errors: {result.errors}")

    def test_tc06_result_has_checks_dict(self):
        """TC-06: result.checks는 dict 타입."""
        result = ServePlaneValidator().validate()
        self.assertIsInstance(result.checks, dict)

    def test_tc07_result_checks_11_checkpoints(self):
        """TC-07: 11개 체크포인트 존재."""
        result = ServePlaneValidator().validate()
        self.assertEqual(len(result.checks), 11)

    def test_tc08_result_errors_is_list(self):
        """TC-08: result.errors는 list."""
        result = ServePlaneValidator().validate()
        self.assertIsInstance(result.errors, list)

    def test_tc09_result_warnings_is_list(self):
        """TC-09: result.warnings는 list."""
        result = ServePlaneValidator().validate()
        self.assertIsInstance(result.warnings, list)

    def test_tc10_chart_name_in_result(self):
        """TC-10: result.chart_name 속성 존재."""
        result = ServePlaneValidator().validate()
        self.assertTrue(hasattr(result, "chart_name"))


# ─────────────────────────────────────────────
# TC-11~20: TestServePlaneValidatorMethods
# ─────────────────────────────────────────────
class TestServePlaneValidatorMethods(unittest.TestCase):
    """개별 validate_* 메서드 단위 테스트 10건."""

    def setUp(self):
        self.v = ServePlaneValidator()

    def test_tc11_validate_chart_yaml_valid(self):
        """TC-11: 유효한 chart 딕셔너리 → (True, [])."""
        ok, errs = self.v.validate_chart_yaml(_valid_chart())
        self.assertTrue(ok, f"Errors: {errs}")
        self.assertEqual(errs, [])

    def test_tc12_validate_chart_yaml_missing_api_version(self):
        """TC-12: apiVersion 누락 → False."""
        chart = _valid_chart()
        del chart["apiVersion"]
        ok, errs = self.v.validate_chart_yaml(chart)
        self.assertFalse(ok)
        self.assertTrue(len(errs) > 0)

    def test_tc13_validate_values_yaml_valid(self):
        """TC-13: 유효한 values 딕셔너리 → (True, [])."""
        ok, errs = self.v.validate_values_yaml(_valid_values())
        self.assertTrue(ok, f"Errors: {errs}")
        self.assertEqual(errs, [])

    def test_tc14_validate_values_yaml_missing_namespace(self):
        """TC-14: namespace 키 누락 → False."""
        vals = _valid_values()
        del vals["namespace"]
        ok, errs = self.v.validate_values_yaml(vals)
        self.assertFalse(ok)

    def test_tc15_validate_namespace_isolation_valid(self):
        """TC-15: literary-serve 네임스페이스 → True."""
        ok, errs = self.v.validate_namespace_isolation(_valid_values())
        self.assertTrue(ok)
        self.assertEqual(errs, [])

    def test_tc16_validate_llm1_promoted_valid(self):
        """TC-16: requirePromoted=True → LLM-1 통과."""
        ok, errs = self.v.validate_llm1_promoted(_valid_values())
        self.assertTrue(ok)
        self.assertEqual(errs, [])

    def test_tc17_validate_cpu_resources_valid(self):
        """TC-17: GPU 없는 CPU 리소스 → True + GPU 에러 없음."""
        ok, errs, warns = self.v.validate_cpu_resources(_valid_values())
        self.assertTrue(ok, f"Errors: {errs}")
        gpu_errs = [e for e in errs if "gpu" in e.lower()]
        self.assertEqual(gpu_errs, [])

    def test_tc18_validate_hpa_config_valid(self):
        """TC-18: 유효한 HPA 설정 → True."""
        ok, errs = self.v.validate_hpa_config(_valid_values())
        self.assertTrue(ok, f"Errors: {errs}")

    def test_tc19_validate_health_check_valid(self):
        """TC-19: healthCheck.enabled=True + 경로 존재 → True."""
        ok, errs = self.v.validate_health_check(_valid_values())
        self.assertTrue(ok, f"Errors: {errs}")

    def test_tc20_validate_template_files_exist(self):
        """TC-20: deployment.yaml + service.yaml + hpa.yaml 모두 존재 → True."""
        ok, errs = self.v.validate_template_files()
        self.assertTrue(ok, f"Template errors: {errs}")


# ─────────────────────────────────────────────
# TC-21~30: TestLLM1AndNamespaceIsolation
# ─────────────────────────────────────────────
class TestLLM1AndNamespaceIsolation(unittest.TestCase):
    """LLM-1 원칙 + 네임스페이스 격리 10건."""

    def setUp(self):
        self.v = ServePlaneValidator()

    def test_tc21_llm1_require_promoted_false_fails(self):
        """TC-21: requirePromoted=False → LLM-1 위반 에러."""
        vals = _valid_values()
        vals["model"]["requirePromoted"] = False
        ok, errs = self.v.validate_llm1_promoted(vals)
        self.assertFalse(ok)
        self.assertTrue(any("promoted" in e.lower() or "LLM-1" in e or "ADR-058" in e for e in errs))

    def test_tc22_llm1_require_promoted_missing_fails(self):
        """TC-22: requirePromoted 키 없음 → False."""
        vals = _valid_values()
        del vals["model"]["requirePromoted"]
        ok, errs = self.v.validate_llm1_promoted(vals)
        self.assertFalse(ok)

    def test_tc23_namespace_literary_train_forbidden(self):
        """TC-23: namespace=literary-train → 격리 위반 에러."""
        vals = _valid_values()
        vals["namespace"] = "literary-train"
        ok, errs = self.v.validate_namespace_isolation(vals)
        self.assertFalse(ok)
        self.assertTrue(any("literary-train" in e for e in errs))

    def test_tc24_namespace_default_forbidden(self):
        """TC-24: namespace=default → 금지 네임스페이스 에러."""
        vals = _valid_values()
        vals["namespace"] = "default"
        ok, errs = self.v.validate_namespace_isolation(vals)
        self.assertFalse(ok)

    def test_tc25_namespace_kube_system_forbidden(self):
        """TC-25: namespace=kube-system → 금지 에러."""
        vals = _valid_values()
        vals["namespace"] = "kube-system"
        ok, errs = self.v.validate_namespace_isolation(vals)
        self.assertFalse(ok)

    def test_tc26_namespace_literary_serve_allowed(self):
        """TC-26: namespace=literary-serve → 허용."""
        vals = _valid_values()
        vals["namespace"] = "literary-serve"
        ok, errs = self.v.validate_namespace_isolation(vals)
        self.assertTrue(ok)

    def test_tc27_llm1_model_section_missing_fails(self):
        """TC-27: model 섹션 전체 누락 → False."""
        vals = _valid_values()
        del vals["model"]
        ok, errs = self.v.validate_llm1_promoted(vals)
        self.assertFalse(ok)

    def test_tc28_namespace_check_in_full_validate(self):
        """TC-28: 전체 validate()에서 namespace_isolation 체크포인트 확인."""
        result = ServePlaneValidator().validate()
        self.assertIn("namespace_isolation", result.checks)
        self.assertTrue(result.checks["namespace_isolation"])

    def test_tc29_llm1_check_in_full_validate(self):
        """TC-29: 전체 validate()에서 llm1_require_promoted 체크포인트 True."""
        result = ServePlaneValidator().validate()
        self.assertIn("llm1_require_promoted", result.checks)
        self.assertTrue(result.checks["llm1_require_promoted"])

    def test_tc30_chart_yaml_wrong_api_version_fails(self):
        """TC-30: apiVersion=v1(구버전) → 에러."""
        chart = _valid_chart()
        chart["apiVersion"] = "v1"
        ok, errs = self.v.validate_chart_yaml(chart)
        self.assertFalse(ok)


# ─────────────────────────────────────────────
# TC-31~40: TestCPUResourcesAndHPA
# ─────────────────────────────────────────────
class TestCPUResourcesAndHPA(unittest.TestCase):
    """CPU 리소스 + HPA 검증 10건."""

    def setUp(self):
        self.v = ServePlaneValidator()

    def test_tc31_gpu_in_requests_forbidden(self):
        """TC-31: requests에 nvidia.com/gpu 포함 → CPU-only 위반 에러."""
        vals = _valid_values()
        vals["resources"]["requests"]["nvidia.com/gpu"] = "1"
        ok, errs, warns = self.v.validate_cpu_resources(vals)
        self.assertFalse(ok)
        self.assertTrue(any("gpu" in e.lower() for e in errs))

    def test_tc32_gpu_in_limits_forbidden(self):
        """TC-32: limits에 nvidia.com/gpu 포함 → 에러."""
        vals = _valid_values()
        vals["resources"]["limits"]["nvidia.com/gpu"] = "1"
        ok, errs, warns = self.v.validate_cpu_resources(vals)
        self.assertFalse(ok)

    def test_tc33_cpu_resource_missing_requests_fails(self):
        """TC-33: resources.requests에 cpu 키 없음 → False."""
        vals = _valid_values()
        del vals["resources"]["requests"]["cpu"]
        ok, errs, warns = self.v.validate_cpu_resources(vals)
        self.assertFalse(ok)

    def test_tc34_hpa_min_replicas_less_than_1_fails(self):
        """TC-34: minReplicas=0 → HPA 에러."""
        vals = _valid_values()
        vals["autoscaling"]["minReplicas"] = 0
        ok, errs = self.v.validate_hpa_config(vals)
        self.assertFalse(ok)

    def test_tc35_hpa_max_less_than_min_fails(self):
        """TC-35: maxReplicas < minReplicas → 에러."""
        vals = _valid_values()
        vals["autoscaling"]["minReplicas"] = 5
        vals["autoscaling"]["maxReplicas"] = 2
        ok, errs = self.v.validate_hpa_config(vals)
        self.assertFalse(ok)

    def test_tc36_hpa_cpu_utilization_out_of_range_fails(self):
        """TC-36: CPU utilization > 100 → 에러."""
        vals = _valid_values()
        vals["autoscaling"]["targetCPUUtilizationPercentage"] = 120
        ok, errs = self.v.validate_hpa_config(vals)
        self.assertFalse(ok)

    def test_tc37_hpa_disabled_no_error(self):
        """TC-37: autoscaling.enabled=False → HPA 체크 스킵 (에러 없음)."""
        vals = _valid_values()
        vals["autoscaling"]["enabled"] = False
        ok, errs = self.v.validate_hpa_config(vals)
        self.assertTrue(ok)

    def test_tc38_hpa_memory_utilization_zero_fails(self):
        """TC-38: Memory utilization = 0 → 에러 (유효 범위 1~100)."""
        vals = _valid_values()
        vals["autoscaling"]["targetMemoryUtilizationPercentage"] = 0
        vals["autoscaling"]["enabled"] = True
        ok, errs = self.v.validate_hpa_config(vals)
        self.assertFalse(ok, f"Expected fail but got ok. errs={errs}")

    def test_tc39_resources_limits_missing_cpu_fails(self):
        """TC-39: resources.limits에 cpu 키 없음 → cpu_resources False."""
        vals = _valid_values()
        del vals["resources"]["limits"]["cpu"]
        ok, errs, warns = self.v.validate_cpu_resources(vals)
        self.assertFalse(ok)

    def test_tc40_cpu_only_check_in_full_validate(self):
        """TC-40: 전체 validate() cpu_resources_valid 체크포인트 True."""
        result = ServePlaneValidator().validate()
        self.assertIn("cpu_resources_valid", result.checks)
        self.assertTrue(result.checks["cpu_resources_valid"])


# ─────────────────────────────────────────────
# TC-41~50: TestEdgeCasesAndIntegration
# ─────────────────────────────────────────────
class TestEdgeCasesAndIntegration(unittest.TestCase):
    """엣지 케이스 + 통합 시나리오 10건."""

    def setUp(self):
        self.v = ServePlaneValidator()

    def test_tc41_health_check_disabled_passes(self):
        """TC-41: healthCheck.enabled=False → 에러 없음 (경고 허용)."""
        vals = _valid_values()
        vals["healthCheck"]["enabled"] = False
        ok, errs = self.v.validate_health_check(vals)
        self.assertTrue(ok)

    def test_tc42_health_check_missing_liveness_path_fails(self):
        """TC-42: livenessPath 누락 → False."""
        vals = _valid_values()
        del vals["healthCheck"]["livenessPath"]
        ok, errs = self.v.validate_health_check(vals)
        self.assertFalse(ok)

    def test_tc43_health_check_missing_readiness_path_fails(self):
        """TC-43: readinessPath 누락 → False."""
        vals = _valid_values()
        del vals["healthCheck"]["readinessPath"]
        ok, errs = self.v.validate_health_check(vals)
        self.assertFalse(ok)

    def test_tc44_serving_params_port_zero_fails(self):
        """TC-44: serving.port=0 → 에러."""
        vals = _valid_values()
        vals["serving"]["port"] = 0
        ok, errs, warns = self.v.validate_serving_params(vals)
        self.assertFalse(ok)

    def test_tc45_serving_params_workers_zero_fails(self):
        """TC-45: serving.workers=0 → 에러."""
        vals = _valid_values()
        vals["serving"]["workers"] = 0
        ok, errs, warns = self.v.validate_serving_params(vals)
        self.assertFalse(ok)

    def test_tc46_serving_log_level_invalid_fails(self):
        """TC-46: logLevel=VERBOSE (비표준) → 에러."""
        vals = _valid_values()
        vals["serving"]["logLevel"] = "VERBOSE"
        ok, errs, warns = self.v.validate_serving_params(vals)
        self.assertFalse(ok)

    def test_tc47_service_account_default_name_warns(self):
        """TC-47: serviceAccount.name='default' → 경고 발생."""
        vals = _valid_values()
        vals["serviceAccount"]["name"] = "default"
        ok, warns = self.v.validate_service_account(vals)
        self.assertTrue(ok)  # 에러 아님 — 경고만
        self.assertTrue(len(warns) > 0)

    def test_tc48_serve_plane_chart_spec_defaults(self):
        """TC-48: ServePlaneChartSpec 기본값 검증."""
        spec = ServePlaneChartSpec()
        self.assertEqual(spec.chart_name, "literary-os-serve-plane")
        self.assertEqual(spec.namespace, "literary-serve")
        self.assertTrue(spec.require_promoted)

    def test_tc49_serve_plane_values_spec_defaults(self):
        """TC-49: ServePlaneValuesSpec 기본값 검증."""
        spec = ServePlaneValuesSpec()
        self.assertEqual(spec.namespace, "literary-serve")
        self.assertTrue(spec.require_promoted)

    def test_tc50_full_validate_all_11_checks_pass(self):
        """TC-50: 전체 validate() — 11개 체크포인트 모두 True."""
        result = ServePlaneValidator().validate()
        failed = [k for k, v in result.checks.items() if not v]
        self.assertEqual(failed, [], f"Failed checkpoints: {failed}")
        self.assertTrue(result.valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
