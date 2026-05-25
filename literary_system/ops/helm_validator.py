"""
SP-B.4 (V626) — HelmValidator: TrainPlane Helm Chart 구조 검증

Phase B 본안 v3.0 §7:
- deploy/helm/train_plane/ Chart.yaml + values.yaml 스키마 검증
- 네임스페이스 격리 확인 (literary-train ≠ literary-serve)
- GPU 리소스 요구사항 검증
- 비용 SLO 논리 검증 (soft < hard < emergency)
- LoRA 하이퍼파라미터 범위 검증
- 템플릿 파일 존재 여부 검증

ADR-093 참조.

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
    "image", "loraJob", "resources", "costSlo", "persistence", "namespace",
    "serviceAccount", "nodeSelector", "tolerations", "provenance",
)

REQUIRED_LORA_JOB_KEYS: Tuple[str, ...] = (
    "baseModel", "loraRank", "loraAlpha", "loraDropout",
    "numEpochs", "batchSize", "scheduleType", "datasetMount", "outputDir",
)

REQUIRED_COST_SLO_KEYS: Tuple[str, ...] = (
    "softUsd", "hardUsd", "emergencyUsd", "monthlyTargetUsd",
)

REQUIRED_RESOURCES_KEYS: Tuple[str, ...] = ("requests", "limits")

REQUIRED_TEMPLATE_FILES: Tuple[str, ...] = ("lora-job.yaml", "cronjob.yaml")

# 네임스페이스 격리 정책 (ADR-057 §5)
NAMESPACE_TRAIN_ALLOWED = "literary-train"
NAMESPACE_FORBIDDEN: Tuple[str, ...] = ("literary-serve", "default", "kube-system")

# LoRA 하이퍼파라미터 허용 범위
LORA_RANK_VALID: Tuple[int, ...] = (4, 8, 16, 32, 64, 128)
LORA_RANK_MIN = 4
LORA_RANK_MAX = 128
LORA_ALPHA_MIN_RATIO = 1.0   # alpha >= rank
LORA_DROPOUT_MIN = 0.0
LORA_DROPOUT_MAX = 0.5
NUM_EPOCHS_MIN = 1
NUM_EPOCHS_MAX = 20
VALID_SCHEDULE_TYPES: Tuple[str, ...] = (
    "full_biweekly", "fine_weekly", "on_demand",
)


# ──────────────────────────────────────────────────────────────────────────────
# 데이터 클래스
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class HelmValidationResult:
    """HelmValidator 검증 결과."""

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
            f"HelmValidator {status} | {chart_name} | "
            f"체크포인트 {n_pass}/{n_total} | "
            f"에러 {len(self.errors)}건 경고 {len(self.warnings)}건"
        ).replace("chart_name", self.chart_name)


@dataclass
class TrainPlaneChartSpec:
    """TrainPlane Helm Chart 기대 스펙 (상수 모음)."""

    chart_name: str = "literary-os-train-plane"
    api_version: str = CHART_API_VERSION
    chart_type: str = CHART_TYPE_APPLICATION
    namespace: str = NAMESPACE_TRAIN_ALLOWED
    required_template_files: Tuple[str, ...] = field(
        default_factory=lambda: REQUIRED_TEMPLATE_FILES
    )


# ──────────────────────────────────────────────────────────────────────────────
# HelmValidator
# ──────────────────────────────────────────────────────────────────────────────

class HelmValidator:
    """TrainPlane Helm Chart 구조 + 스키마 검증기.

    V626 신규. ADR-093 참조.
    LLM-0 원칙 준수 (외부 LLM API 호출 없음).
    """

    VERSION = "1.0.0"
    DEFAULT_CHART_DIR = "deploy/helm/train_plane"

    def __init__(self, chart_dir: Optional[str] = None) -> None:
        self.chart_dir = Path(chart_dir or self.DEFAULT_CHART_DIR)
        self._spec = TrainPlaneChartSpec()

    # ── 공개 인터페이스 ──────────────────────────────────────────────────────

    def validate(self) -> HelmValidationResult:
        """Chart.yaml + values.yaml + 템플릿 파일 전체 검증."""
        errors: List[str] = []
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        # 1. 차트 디렉토리 존재 확인
        dir_ok = self.chart_dir.is_dir()
        checks["chart_dir_exists"] = dir_ok
        if not dir_ok:
            errors.append(f"차트 디렉토리 없음: {self.chart_dir}")
            return HelmValidationResult(
                valid=False, chart_name="unknown",
                chart_dir=str(self.chart_dir),
                errors=errors, warnings=warnings, checks=checks
            )

        # 2. Chart.yaml 로드 + 검증
        chart_data = self._load_yaml(self.chart_dir / "Chart.yaml")
        chart_ok, chart_errs = self.validate_chart_yaml(chart_data)
        checks["chart_yaml_valid"] = chart_ok
        errors.extend(chart_errs)

        chart_name = chart_data.get("name", "unknown") if chart_data else "unknown"

        # 3. values.yaml 로드 + 검증
        values_data = self._load_yaml(self.chart_dir / "values.yaml")
        values_ok, values_errs = self.validate_values_yaml(values_data)
        checks["values_yaml_valid"] = values_ok
        errors.extend(values_errs)

        # 4. 네임스페이스 격리 검증
        ns_ok, ns_errs = self.validate_namespace_isolation(values_data)
        checks["namespace_isolation"] = ns_ok
        errors.extend(ns_errs)

        # 5. GPU 리소스 검증
        gpu_ok, gpu_errs = self.validate_gpu_resources(values_data)
        checks["gpu_resources_valid"] = gpu_ok
        errors.extend(gpu_errs)

        # 6. 비용 SLO 논리 검증
        slo_ok, slo_errs = self.validate_cost_slo(values_data)
        checks["cost_slo_valid"] = slo_ok
        errors.extend(slo_errs)

        # 7. LoRA 하이퍼파라미터 범위 검증
        lora_ok, lora_errs, lora_warns = self.validate_lora_hyperparams(values_data)
        checks["lora_hyperparams_valid"] = lora_ok
        errors.extend(lora_errs)
        warnings.extend(lora_warns)

        # 8. 템플릿 파일 존재 검증
        tmpl_ok, tmpl_errs = self.validate_template_files()
        checks["template_files_exist"] = tmpl_ok
        errors.extend(tmpl_errs)

        # 9. 서비스 어카운트 검증
        sa_ok, sa_warns = self.validate_service_account(values_data)
        checks["service_account_valid"] = sa_ok
        warnings.extend(sa_warns)

        valid = len(errors) == 0
        if valid:
            logger.info("HelmValidator PASS: %s (%d 체크포인트 전통과)", chart_name, len(checks))
        else:
            logger.warning(
                "HelmValidator FAIL: %s — 에러 %d건", chart_name, len(errors)
            )

        return HelmValidationResult(
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
        """Chart.yaml 필수 필드 + apiVersion + type 검증."""
        errors: List[str] = []
        if chart is None:
            errors.append("Chart.yaml 로드 실패")
            return False, errors

        for field_name in REQUIRED_CHART_FIELDS:
            if field_name not in chart:
                errors.append(f"Chart.yaml 필수 필드 누락: {field_name}")

        api_ver = chart.get("apiVersion", "")
        if api_ver != CHART_API_VERSION:
            errors.append(
                f"Chart.yaml apiVersion 오류: 기대={CHART_API_VERSION!r}, 실제={api_ver!r}"
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
        """values.yaml 최상위 필수 키 + 타입 검증."""
        errors: List[str] = []
        if values is None:
            errors.append("values.yaml 로드 실패")
            return False, errors

        for key in REQUIRED_VALUES_KEYS:
            if key not in values:
                errors.append(f"values.yaml 필수 키 누락: {key}")

        # loraJob 하위 키 검증
        lora_job = values.get("loraJob", {})
        if isinstance(lora_job, dict):
            for key in REQUIRED_LORA_JOB_KEYS:
                if key not in lora_job:
                    errors.append(f"values.loraJob 필수 키 누락: {key}")
        else:
            errors.append("values.loraJob 타입 오류: dict 기대")

        # costSlo 하위 키 검증
        cost_slo = values.get("costSlo", {})
        if isinstance(cost_slo, dict):
            for key in REQUIRED_COST_SLO_KEYS:
                if key not in cost_slo:
                    errors.append(f"values.costSlo 필수 키 누락: {key}")
        else:
            errors.append("values.costSlo 타입 오류: dict 기대")

        # resources 하위 키 검증
        resources = values.get("resources", {})
        if isinstance(resources, dict):
            for key in REQUIRED_RESOURCES_KEYS:
                if key not in resources:
                    errors.append(f"values.resources 필수 키 누락: {key}")
        else:
            errors.append("values.resources 타입 오류: dict 기대")

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
                f"네임스페이스 격리 위반: '{ns}'는 TrainPlane에 사용 불가 "
                f"(금지 목록: {NAMESPACE_FORBIDDEN})"
            )

        if ns != NAMESPACE_TRAIN_ALLOWED:
            errors.append(
                f"TrainPlane 네임스페이스 오류: 기대='{NAMESPACE_TRAIN_ALLOWED}', 실제='{ns}'"
            )

        return len(errors) == 0, errors

    def validate_gpu_resources(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """GPU 리소스 요청/한계 검증 (TrainPlane 전용)."""
        errors: List[str] = []
        if not values:
            return True, errors

        resources = values.get("resources", {})
        if not isinstance(resources, dict):
            return True, errors

        for section in ("requests", "limits"):
            sec = resources.get(section, {})
            if not isinstance(sec, dict):
                errors.append(f"resources.{section} 타입 오류")
                continue

            gpu_val = sec.get("nvidia.com/gpu")
            if gpu_val is None:
                errors.append(f"resources.{section}['nvidia.com/gpu'] 누락 — TrainPlane은 GPU 필수")
            else:
                try:
                    if int(gpu_val) < 1:
                        errors.append(
                            f"resources.{section}['nvidia.com/gpu'] 값 오류: {gpu_val} < 1"
                        )
                except (ValueError, TypeError):
                    errors.append(
                        f"resources.{section}['nvidia.com/gpu'] 파싱 오류: {gpu_val!r}"
                    )

        return len(errors) == 0, errors

    def validate_cost_slo(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """비용 SLO 논리 검증: soft < hard < emergency."""
        errors: List[str] = []
        if not values:
            return True, errors

        cost_slo = values.get("costSlo", {})
        if not isinstance(cost_slo, dict):
            return True, errors

        try:
            soft = float(cost_slo.get("softUsd", 0))
            hard = float(cost_slo.get("hardUsd", 0))
            emrg = float(cost_slo.get("emergencyUsd", 0))
            monthly = float(cost_slo.get("monthlyTargetUsd", 0))
        except (TypeError, ValueError) as exc:
            errors.append(f"costSlo 수치 파싱 오류: {exc}")
            return False, errors

        if not (0 < soft < hard):
            errors.append(
                f"costSlo 논리 오류: softUsd({soft}) < hardUsd({hard}) 조건 불만족"
            )

        if not (hard < emrg):
            errors.append(
                f"costSlo 논리 오류: hardUsd({hard}) < emergencyUsd({emrg}) 조건 불만족"
            )

        if not (0 < monthly <= hard):
            errors.append(
                f"costSlo 논리 오류: monthlyTargetUsd({monthly}) <= hardUsd({hard}) 조건 불만족 "
                f"(ADR-057: 월 예산 목표는 하드 한도 이하여야 함)"
            )

        return len(errors) == 0, errors

    def validate_lora_hyperparams(
        self, values: Optional[Dict[str, Any]]
    ) -> Tuple[bool, List[str], List[str]]:
        """LoRA 하이퍼파라미터 범위 검증."""
        errors: List[str] = []
        warnings: List[str] = []
        if not values:
            return True, errors, warnings

        lora_job = values.get("loraJob", {})
        if not isinstance(lora_job, dict):
            return True, errors, warnings

        # loraRank 검증
        lora_rank = lora_job.get("loraRank")
        if lora_rank is not None:
            try:
                rank = int(lora_rank)
                if rank not in LORA_RANK_VALID:
                    warnings.append(
                        f"loraRank={rank} 권장 범위 외 "
                        f"(권장: {LORA_RANK_VALID})"
                    )
                if not (LORA_RANK_MIN <= rank <= LORA_RANK_MAX):
                    errors.append(
                        f"loraRank={rank} 범위 초과 "
                        f"({LORA_RANK_MIN}~{LORA_RANK_MAX})"
                    )
            except (TypeError, ValueError):
                errors.append(f"loraRank 파싱 오류: {lora_rank!r}")
                rank = None
        else:
            rank = None

        # loraAlpha 검증 (alpha >= rank)
        lora_alpha = lora_job.get("loraAlpha")
        if lora_alpha is not None and rank is not None:
            try:
                alpha = int(lora_alpha)
                if alpha < rank:
                    errors.append(
                        f"loraAlpha({alpha}) < loraRank({rank}) — alpha >= rank 필요"
                    )
            except (TypeError, ValueError):
                errors.append(f"loraAlpha 파싱 오류: {lora_alpha!r}")

        # loraDropout 범위
        dropout = lora_job.get("loraDropout")
        if dropout is not None:
            try:
                d = float(dropout)
                if not (LORA_DROPOUT_MIN <= d <= LORA_DROPOUT_MAX):
                    errors.append(
                        f"loraDropout={d} 범위 초과 "
                        f"({LORA_DROPOUT_MIN}~{LORA_DROPOUT_MAX})"
                    )
            except (TypeError, ValueError):
                errors.append(f"loraDropout 파싱 오류: {dropout!r}")

        # numEpochs 범위
        epochs = lora_job.get("numEpochs")
        if epochs is not None:
            try:
                e = int(epochs)
                if not (NUM_EPOCHS_MIN <= e <= NUM_EPOCHS_MAX):
                    errors.append(
                        f"numEpochs={e} 범위 초과 "
                        f"({NUM_EPOCHS_MIN}~{NUM_EPOCHS_MAX})"
                    )
            except (TypeError, ValueError):
                errors.append(f"numEpochs 파싱 오류: {epochs!r}")

        # scheduleType 검증
        sched = lora_job.get("scheduleType", "")
        if sched and sched not in VALID_SCHEDULE_TYPES:
            errors.append(
                f"scheduleType='{sched}' 허용 값 외 "
                f"(허용: {VALID_SCHEDULE_TYPES})"
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
        """서비스 어카운트 설정 검증 (경고만)."""
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
            warnings.append("serviceAccount.name 미설정 — 기본 SA 사용 주의")
        elif sa_name == "default":
            warnings.append(
                "serviceAccount.name='default' — 전용 SA 이름 사용 권고"
            )

        return True, warnings

    # ── 내부 유틸 ────────────────────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: Path) -> Optional[Dict[str, Any]]:
        """YAML 파일 로드. yaml 없으면 간단 파서 사용."""
        if not path.is_file():
            logger.warning("파일 없음: %s", path)
            return None
        try:
            import yaml  # type: ignore[import]
            with path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except ImportError:
            pass

        # yaml 모듈 없을 때 최소 파서
        return HelmValidator._minimal_yaml_parse(path)

    @staticmethod
    def _minimal_yaml_parse(path: Path) -> Dict[str, Any]:
        """PyYAML 없는 환경에서 단순 key: value 파싱 (중첩 지원 없음 — 최상위만)."""
        result: Dict[str, Any] = {}
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                    continue
                if ":" in stripped and not stripped.startswith(" "):
                    key, _, val = stripped.partition(":")
                    val = val.strip().strip('"').strip("'")
                    if val:
                        result[key.strip()] = val
                    else:
                        result[key.strip()] = {}
        return result
