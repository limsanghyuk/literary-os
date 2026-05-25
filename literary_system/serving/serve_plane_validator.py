"""
SP-B.4 (V627) — ServePlaneValidator: ServePlane Helm Chart 구조 검증

Phase B 본안 v3.0 §8:
- deploy/helm/serve_plane/ Chart.yaml + values.yaml 스키마 검증
- 네임스페이스 격리 확인 (literary-serve ≠ literary-train)
- LLM-1 원칙 강제: requirePromoted=true 필수 (ADR-058)
- CPU 리소스 요구사항 검증 (ServePlane은 GPU 없이 CPU 추론)
- HPA 설정 논리 검증 (minReplicas <= maxReplicas)
- 헬스체크 경로 형식 검증
- 오토스케일링 임계값 검증

ADR-094 참조.

LLM-0 원칙: 이 모듈은 외부 LLM API를 직접 호출하지 않음.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────────────────────────────

CHART_API_VERSION = "v2"
CHART_TYPE_APPLICATION = "application"

REQUIRED_CHART_FIELDS: Tuple[str, ...] = (
    "apiVersion", "name", "version", "appVersion", "description", "type"
)

REQUIRED_VALUES_KEYS: Tuple[str, ...] = (
    "image", "serving", "model", "replicaCount", "resources",
    "namespace", "serviceAccount", "service", "autoscaling",
    "healthCheck", "persistence",
)

REQUIRED_SERVING_KEYS: Tuple[str, ...] = (
    "port", "workers", "timeoutSec", "maxConcurrent", "logLevel",
)

REQUIRED_MODEL_KEYS: Tuple[str, ...] = (
    "baseModel", "modelMount", "requirePromoted", "maxSeqLen", "batchSize",
)

REQUIRED_AUTOSCALING_KEYS: Tuple[str, ...] = (
    "enabled", "minReplicas", "maxReplicas",
    "targetCPUUtilizationPercentage", "targetMemoryUtilizationPercentage",
)

REQUIRED_HEALTH_KEYS: Tuple[str, ...] = (
    "enabled", "livenessPath", "readinessPath",
    "initialDelaySeconds", "periodSeconds", "failureThreshold",
)

REQUIRED_TEMPLATE_FILES: Tuple[str, ...] = (
    "deployment.yaml", "service.yaml", "hpa.yaml"
)

# 네임스페이스 격리 정책 (ADR-057 §5)
NAMESPACE_SERVE_ALLOWED = "literary-serve"
NAMESPACE_FORBIDDEN: Tuple[str, ...] = ("literary-train", "default", "kube-system")

# 서빙 설정 허용 범위
SERVE_PORT_MIN = 1024
SERVE_PORT_MAX = 65535
WORKERS_MIN = 1
WORKERS_MAX = 32
TIMEOUT_MIN = 1
TIMEOUT_MAX = 300
MAX_CONCURRENT_MIN = 1

# HPA 설정 허용 범위
MIN_REPLICAS_MIN = 1
MAX_REPLICAS_MAX = 100
CPU_UTIL_MIN = 10
CPU_UTIL_MAX = 100
MEM_UTIL_MIN = 10
MEM_UTIL_MAX = 100

# 유효한 로그 레벨
VALID_LOG_LEVELS: Tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

# 서비스 타입
VALID_SERVICE_TYPES: Tuple[str, ...] = ("ClusterIP", "NodePort", "LoadBalancer")


# ──────────────────────────────────────────────────────────────────────────────
# 데이터 클래스
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ServePlaneValidationResult:
    """ServePlaneValidator 검증 결과."""

    valid: bool
    chart_name: str
    chart_dir: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks: Dict[str, bool] = field(default_factory=dict)

    def summary(self) -> str:
        status = "PASS" if self.valid else "FAIL"
        n_pass = sum(1 for v in self.checks.values() if v)
        n_total = len(self.checks)
        return (
            f"ServePlaneValidator {status} | {self.chart_name} | "
            f"체크포인트 {n_pass}/{n_total} | "
            f"에러 {len(self.errors)}건 경고 {len(self.warnings)}건"
        )


@dataclass
class ServePlaneChartSpec:
    """ServePlane Helm Chart 기대 스펙 상수 집합."""

    chart_name: str = "literary-os-serve-plane"
    api_version: str = CHART_API_VERSION
    chart_type: str = CHART_TYPE_APPLICATION
    namespace: str = NAMESPACE_SERVE_ALLOWED
    required_template_files: Tuple[str, ...] = field(
        default_factory=lambda: REQUIRED_TEMPLATE_FILES
    )
    require_promoted: bool = True   # LLM-1 원칙 (ADR-058)


@dataclass
class ServePlaneValuesSpec:
    """ServePlane values.yaml 기대 스펙."""

    namespace: str = NAMESPACE_SERVE_ALLOWED
    min_replicas: int = 1
    max_replicas: int = 8
    serve_port: int = 8080
    log_level: str = "INFO"
    require_promoted: bool = True


# ──────────────────────────────────────────────────────────────────────────────
# ServePlaneValidator
# ──────────────────────────────────────────────────────────────────────────────

class ServePlaneValidator:
    """ServePlane Helm Chart 구조 + 스키마 검증기.

    V627 신규. ADR-094 참조.
    LLM-0 원칙 준수 (외부 LLM API 호출 없음).
    LLM-1 원칙 강제: requirePromoted=true 검증.
    """

    VERSION = "1.0.0"
    DEFAULT_CHART_DIR = "deploy/helm/serve_plane"

    def __init__(self, chart_dir: Optional[str] = None) -> None:
        self.chart_dir = Path(chart_dir or self.DEFAULT_CHART_DIR)
        self._spec = ServePlaneChartSpec()

    # ── 공개 인터페이스 ──────────────────────────────────────────────────────

    def validate(self) -> ServePlaneValidationResult:
        """Chart.yaml + values.yaml + 템플릿 파일 전체 검증."""
        errors: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        # 1. 차트 디렉토리 존재
        dir_ok = self.chart_dir.is_dir()
        checks["chart_dir_exists"] = dir_ok
        if not dir_ok:
            errors.append(f"차트 디렉토리 없음: {self.chart_dir}")
            return ServePlaneValidationResult(
                valid=False, chart_name="unknown",
                chart_dir=str(self.chart_dir),
                errors=errors, warnings=warnings, checks=checks
            )

        # 2. Chart.yaml
        chart_data = self._load_yaml(self.chart_dir / "Chart.yaml")
        chart_ok, chart_errs = self.validate_chart_yaml(chart_data)
        checks["chart_yaml_valid"] = chart_ok
        errors.extend(chart_errs)
        chart_name = chart_data.get("name", "unknown") if chart_data else "unknown"

        # 3. values.yaml
        values_data = self._load_yaml(self.chart_dir / "values.yaml")
        values_ok, values_errs = self.validate_values_yaml(values_data)
        checks["values_yaml_valid"] = values_ok
        errors.extend(values_errs)

        # 4. 네임스페이스 격리
        ns_ok, ns_errs = self.validate_namespace_isolation(values_data)
        checks["namespace_isolation"] = ns_ok
        errors.extend(ns_errs)

        # 5. LLM-1 원칙 (requirePromoted)
        llm1_ok, llm1_errs = self.validate_llm1_promoted(values_data)
        checks["llm1_require_promoted"] = llm1_ok
        errors.extend(llm1_errs)

        # 6. CPU 리소스 (ServePlane은 GPU 없음)
        cpu_ok, cpu_errs, cpu_warns = self.validate_cpu_resources(values_data)
        checks["cpu_resources_valid"] = cpu_ok
        errors.extend(cpu_errs)
        warnings.extend(cpu_warns)

        # 7. HPA 설정 논리
        hpa_ok, hpa_errs = self.validate_hpa_config(values_data)
        checks["hpa_config_valid"] = hpa_ok
        errors.extend(hpa_errs)

        # 8. 헬스체크 경로
        hc_ok, hc_errs = self.validate_health_check(values_data)
        checks["health_check_valid"] = hc_ok
        errors.extend(hc_errs)

        # 9. 서빙 파라미터 범위
        srv_ok, srv_errs, srv_warns = self.validate_serving_params(values_data)
        checks["serving_params_valid"] = srv_ok
        errors.extend(srv_errs)
        warnings.extend(srv_warns)

        # 10. 템플릿 파일
        tmpl_ok, tmpl_errs = self.validate_template_files()
        checks["template_files_exist"] = tmpl_ok
        errors.extend(tmpl_errs)

        # 11. 서비스 어카운트 (경고)
        sa_ok, sa_warns = self.validate_service_account(values_data)
        checks["service_account_valid"] = sa_ok
        warnings.extend(sa_warns)

        valid = len(errors) == 0
        if valid:
            logger.info(
                "ServePlaneValidator PASS: %s (%d 체크포인트 전통과)", chart_name, len(checks)
            )
        else:
            logger.warning(
                "ServePlaneValidator FAIL: %s — 에러 %d건", chart_name, len(errors)
            )

        return ServePlaneValidationResult(
            valid=valid,
            chart_name=chart_name,
            chart_dir=str(self.chart_dir),
            errors=errors,
            warnings=warnings,
            checks=checks,
        )

    # ── 개별 검증 메서드 ─────────────────────────────────────────────────────

    def validate_chart_yaml(
        self, chart: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """Chart.yaml 필수 필드 + apiVersion 검증."""
        errors: List[str] = []
        if chart is None:
            errors.append("Chart.yaml 로드 실패")
            return False, errors

        for f in REQUIRED_CHART_FIELDS:
            if f not in chart:
                errors.append(f"Chart.yaml 필수 필드 누락: {f}")

        if chart.get("apiVersion") != CHART_API_VERSION:
            errors.append(
                f"Chart.yaml apiVersion 오류: 기대={CHART_API_VERSION!r}, "
                f"실제={chart.get('apiVersion')!r}"
            )

        chart_type = chart.get("type", "")
        if chart_type and chart_type != CHART_TYPE_APPLICATION:
            errors.append(
                f"Chart.yaml type 오류: 기대={CHART_TYPE_APPLICATION!r}, 실제={chart_type!r}"
            )

        return len(errors) == 0, errors

    def validate_values_yaml(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """values.yaml 최상위 필수 키 + 하위 구조 검증."""
        errors: List[str] = []
        if values is None:
            errors.append("values.yaml 로드 실패")
            return False, errors

        for key in REQUIRED_VALUES_KEYS:
            if key not in values:
                errors.append(f"values.yaml 필수 키 누락: {key}")

        # serving 하위 키
        serving = values.get("serving", {})
        if isinstance(serving, dict):
            for key in REQUIRED_SERVING_KEYS:
                if key not in serving:
                    errors.append(f"values.serving 필수 키 누락: {key}")
        else:
            errors.append("values.serving 타입 오류: dict 기대")

        # model 하위 키
        model = values.get("model", {})
        if isinstance(model, dict):
            for key in REQUIRED_MODEL_KEYS:
                if key not in model:
                    errors.append(f"values.model 필수 키 누락: {key}")
        else:
            errors.append("values.model 타입 오류: dict 기대")

        # autoscaling 하위 키
        autoscaling = values.get("autoscaling", {})
        if isinstance(autoscaling, dict):
            for key in REQUIRED_AUTOSCALING_KEYS:
                if key not in autoscaling:
                    errors.append(f"values.autoscaling 필수 키 누락: {key}")
        else:
            errors.append("values.autoscaling 타입 오류: dict 기대")

        return len(errors) == 0, errors

    def validate_namespace_isolation(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """네임스페이스 격리 정책 검증 (ADR-057 §5)."""
        errors: List[str] = []
        if not values:
            return True, errors

        ns = values.get("namespace", "")
        if not ns:
            errors.append("values.namespace 값 없음")
            return False, errors

        if ns in NAMESPACE_FORBIDDEN:
            errors.append(
                f"네임스페이스 격리 위반: '{ns}'는 ServePlane에 사용 불가 "
                f"(금지 목록: {NAMESPACE_FORBIDDEN})"
            )

        if ns != NAMESPACE_SERVE_ALLOWED:
            errors.append(
                f"ServePlane 네임스페이스 오류: 기대='{NAMESPACE_SERVE_ALLOWED}', 실제='{ns}'"
            )

        return len(errors) == 0, errors

    def validate_llm1_promoted(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """LLM-1 원칙 강제: model.requirePromoted=true (ADR-058)."""
        errors: List[str] = []
        if not values:
            return True, errors

        model = values.get("model", {})
        if not isinstance(model, dict):
            return True, errors

        require_promoted = model.get("requirePromoted")
        if require_promoted is None:
            errors.append(
                "model.requirePromoted 누락 — LLM-1 원칙 위반 (ADR-058: PROMOTED 단계만 서빙)"
            )
        elif require_promoted is False or str(require_promoted).lower() == "false":
            errors.append(
                "model.requirePromoted=false — LLM-1 원칙 위반 "
                "(ADR-058: PROMOTED 단계 모델만 서빙 허용)"
            )

        return len(errors) == 0, errors

    def validate_cpu_resources(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str], List[str]]:
        """CPU 리소스 검증. ServePlane은 GPU 없이 CPU 추론 — GPU 요청 금지."""
        errors: List[str] = []
        warnings: List[str] = []
        if not values:
            return True, errors, warnings

        resources = values.get("resources", {})
        if not isinstance(resources, dict):
            return True, errors, warnings

        for section in ("requests", "limits"):
            sec = resources.get(section, {})
            if not isinstance(sec, dict):
                continue

            # ServePlane: GPU 요청 금지 (TrainPlane과 격리)
            if "nvidia.com/gpu" in sec:
                errors.append(
                    f"resources.{section}['nvidia.com/gpu'] 설정 금지 — "
                    "ServePlane은 CPU 전용 추론 (TrainPlane과 리소스 격리, ADR-057 §5)"
                )

            # CPU 요청 확인 (필수)
            if "cpu" not in sec:
                errors.append(f"resources.{section}.cpu 미설정 — CPU 리소스 설정 필수")

            # 메모리 요청 확인 (필수)
            if "memory" not in sec:
                errors.append(f"resources.{section}.memory 미설정 — 메모리 리소스 설정 필수")

        return len(errors) == 0, errors, warnings

    def validate_hpa_config(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """HPA 설정 논리 검증."""
        errors: List[str] = []
        if not values:
            return True, errors

        autoscaling = values.get("autoscaling", {})
        if not isinstance(autoscaling, dict):
            return True, errors

        if not autoscaling.get("enabled", False):
            return True, errors  # 비활성화 시 검증 생략

        try:
            min_r = int(autoscaling.get("minReplicas", 1))
            max_r = int(autoscaling.get("maxReplicas", 1))
        except (TypeError, ValueError) as exc:
            errors.append(f"autoscaling replicas 파싱 오류: {exc}")
            return False, errors

        if min_r < MIN_REPLICAS_MIN:
            errors.append(f"autoscaling.minReplicas={min_r} < {MIN_REPLICAS_MIN}")

        if max_r > MAX_REPLICAS_MAX:
            errors.append(f"autoscaling.maxReplicas={max_r} > {MAX_REPLICAS_MAX}")

        if min_r > max_r:
            errors.append(
                f"autoscaling 논리 오류: minReplicas({min_r}) > maxReplicas({max_r})"
            )

        cpu_util = autoscaling.get("targetCPUUtilizationPercentage")
        if cpu_util is not None:
            try:
                c = int(cpu_util)
                if not (CPU_UTIL_MIN <= c <= CPU_UTIL_MAX):
                    errors.append(
                        f"targetCPUUtilizationPercentage={c} 범위 오류 "
                        f"({CPU_UTIL_MIN}~{CPU_UTIL_MAX})"
                    )
            except (TypeError, ValueError):
                errors.append(f"targetCPUUtilizationPercentage 파싱 오류: {cpu_util!r}")

        mem_util = autoscaling.get("targetMemoryUtilizationPercentage")
        if mem_util is not None:
            try:
                m = int(mem_util)
                if not (1 <= m <= 100):
                    errors.append(
                        f"targetMemoryUtilizationPercentage={m} 범위 오류 (1~100)"
                    )
            except (TypeError, ValueError):
                errors.append(f"targetMemoryUtilizationPercentage 파싱 오류: {mem_util!r}")

        return len(errors) == 0, errors

    def validate_health_check(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """헬스체크 경로 형식 + 설정 검증."""
        errors: List[str] = []
        if not values:
            return True, errors

        hc = values.get("healthCheck", {})
        if not isinstance(hc, dict) or not hc.get("enabled", False):
            return True, errors

        for path_key in ("livenessPath", "readinessPath"):
            path_val = hc.get(path_key, "")
            if not path_val:
                errors.append(f"healthCheck.{path_key} 누락")
            elif not str(path_val).startswith("/"):
                errors.append(
                    f"healthCheck.{path_key}='{path_val}' 형식 오류 — '/'로 시작해야 함"
                )

        for int_key in ("initialDelaySeconds", "periodSeconds", "failureThreshold"):
            val = hc.get(int_key)
            if val is not None:
                try:
                    if int(val) < 1:
                        errors.append(f"healthCheck.{int_key}={val} < 1")
                except (TypeError, ValueError):
                    errors.append(f"healthCheck.{int_key} 파싱 오류: {val!r}")

        return len(errors) == 0, errors

    def validate_serving_params(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str], List[str]]:
        """서빙 파라미터 범위 검증."""
        errors: List[str] = []
        warnings: List[str] = []
        if not values:
            return True, errors, warnings

        serving = values.get("serving", {})
        if not isinstance(serving, dict):
            return True, errors, warnings

        # 포트 범위
        port = serving.get("port")
        if port is not None:
            try:
                p = int(port)
                if not (SERVE_PORT_MIN <= p <= SERVE_PORT_MAX):
                    errors.append(
                        f"serving.port={p} 범위 오류 ({SERVE_PORT_MIN}~{SERVE_PORT_MAX})"
                    )
            except (TypeError, ValueError):
                errors.append(f"serving.port 파싱 오류: {port!r}")

        # 워커 수
        workers = serving.get("workers")
        if workers is not None:
            try:
                w = int(workers)
                if not (WORKERS_MIN <= w <= WORKERS_MAX):
                    errors.append(
                        f"serving.workers={w} 범위 오류 ({WORKERS_MIN}~{WORKERS_MAX})"
                    )
            except (TypeError, ValueError):
                errors.append(f"serving.workers 파싱 오류: {workers!r}")

        # 타임아웃
        timeout = serving.get("timeoutSec")
        if timeout is not None:
            try:
                t = int(timeout)
                if not (TIMEOUT_MIN <= t <= TIMEOUT_MAX):
                    errors.append(
                        f"serving.timeoutSec={t} 범위 오류 ({TIMEOUT_MIN}~{TIMEOUT_MAX})"
                    )
            except (TypeError, ValueError):
                errors.append(f"serving.timeoutSec 파싱 오류: {timeout!r}")

        # 로그 레벨
        log_level = serving.get("logLevel", "")
        if log_level and log_level not in VALID_LOG_LEVELS:
            errors.append(
                f"serving.logLevel='{log_level}' 허용 값 외 (허용: {VALID_LOG_LEVELS})"
            )

        return len(errors) == 0, errors, warnings

    def validate_template_files(self) -> Tuple[bool, List[str]]:
        """필수 템플릿 파일 존재 검증."""
        errors: List[str] = []
        templates_dir = self.chart_dir / "templates"

        if not templates_dir.is_dir():
            errors.append(f"templates/ 디렉토리 없음: {templates_dir}")
            return False, errors

        for fname in REQUIRED_TEMPLATE_FILES:
            fpath = templates_dir / fname
            if not fpath.is_file():
                errors.append(f"템플릿 파일 없음: {fpath}")

        return len(errors) == 0, errors

    def validate_service_account(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """서비스 어카운트 설정 검증 (경고)."""
        warnings: List[str] = []
        if not values:
            return True, warnings

        sa = values.get("serviceAccount", {})
        if not isinstance(sa, dict):
            warnings.append("values.serviceAccount 타입 오류 — dict 기대")
            return False, warnings

        if not sa.get("create", False):
            warnings.append(
                "serviceAccount.create=false — 전용 SA 생성 권고 (보안 최소 권한)"
            )

        sa_name = sa.get("name", "")
        if not sa_name:
            warnings.append("serviceAccount.name 미설정")
        elif sa_name == "default":
            warnings.append("serviceAccount.name='default' — 전용 SA 이름 사용 권고")

        return True, warnings

    # ── 내부 유틸 ────────────────────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: Path) -> Optional[Dict[str, Any]]:
        if not path.is_file():
            logger.warning("파일 없음: %s", path)
            return None
        try:
            import yaml  # type: ignore[import]
            with path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except ImportError:
            pass
        return ServePlaneValidator._minimal_yaml_parse(path)

    @staticmethod
    def _minimal_yaml_parse(path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                    continue
                if ":" in stripped and not stripped.startswith(" "):
                    key, _, val = stripped.partition(":")
                    val = val.strip().strip('"').strip("'")
                    result[key.strip()] = val if val else {}
        return result
