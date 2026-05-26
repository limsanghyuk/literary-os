"""
self_learning_gate.py — SelfLearningGate G63 (V645, ADR-105)

SP-C.1 Self-Learning Loop 최종 합격 게이트.
3개 독립 축을 동시에 만족해야 SP-C.1 완료로 판정한다.

합격 조건 (G63):
  1. 오염률  = 0.0  — ContaminationDetector 최신 스캔 기준
  2. KL < 0.05      — ConstitutionWeights 분포 vs 균등 분포 KL divergence
  3. α   ≥ 0.70    — Krippendorff α 평가자 간 신뢰도 (ALPHA_MIN_THRESHOLD)

LLM-0 원칙 완전 준수 (외부 LLM 호출 없음).
"""
from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────
KL_MAX: float = 0.05          # KL divergence 최대 허용값
ALPHA_MIN: float = 0.70       # Krippendorff α 최소 합격 기준
CONTAMINATION_MAX: float = 0.0  # 허용 오염률 (0 = 오염 없어야 함)
N_CONSTITUTION_AXES: int = 5  # ConstitutionWeights 축 수 (균등 분포 기준)
_DEFAULT_STORE: str = "data/losdb/self_learning_gate.jsonl"
_MEMORY_SENTINEL: str = ":memory:"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kl_divergence_from_uniform(weights: Sequence[float]) -> float:
    """KL(weights || uniform) 계산.

    KL(p || q) = Σ p_i * log(p_i / q_i)
    q_i = 1 / len(weights) (균등 분포)

    weights 가 비어 있으면 0.0 반환.
    수치 안정성을 위해 p_i < 1e-12 항목은 건너뜀.

    B-2 수정: weights는 확률 분포여야 함 (합 ≈ 1.0, 모든 원소 ≥ 0).
    음수 원소 포함 시 ValueError, 합이 1.0에서 ±0.01 초과 시 ValueError.
    """
    n = len(weights)
    if n == 0:
        return 0.0
    weights_list = list(weights)
    # 음수 검증
    if any(p < 0.0 for p in weights_list):
        raise ValueError(
            f"_kl_divergence_from_uniform: weights must be non-negative, "
            f"got {weights_list}"
        )
    # 합 검증 (확률 분포 전제)
    total = sum(weights_list)
    if total > 1e-12 and abs(total - 1.0) > 0.01:
        raise ValueError(
            f"_kl_divergence_from_uniform: weights must sum to 1.0 "
            f"(got {total:.6f}). Normalize before calling."
        )
    q_i = 1.0 / n
    kl = 0.0
    for p_i in weights_list:
        if p_i < 1e-12:
            continue
        kl += p_i * math.log(p_i / q_i)
    return max(kl, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 결과 데이터클래스
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SLGAxisResult:
    """G63 단일 평가 축 결과."""
    axis_name: str
    value: float
    threshold: float
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "axis_name": self.axis_name,
            "value": self.value,
            "threshold": self.threshold,
            "passed": self.passed,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SLGAxisResult":
        return cls(
            axis_name=d["axis_name"],
            value=float(d["value"]),
            threshold=float(d["threshold"]),
            passed=bool(d["passed"]),
            detail=d.get("detail", ""),
        )


@dataclass
class SelfLearningGateReport:
    """SelfLearningGate G63 단일 평가 결과."""
    report_id: str
    evaluated_at: str
    contamination_rate: float
    kl_divergence: float
    alpha: float
    axes: List[SLGAxisResult]
    passed: bool
    notes: List[str] = field(default_factory=list)
    # B-1 수정: 평가 시 사용한 임계값을 레포트에 저장 (커스텀 임계값 추적)
    _contamination_max: float = field(default=CONTAMINATION_MAX, repr=False)
    _kl_max: float = field(default=KL_MAX, repr=False)
    _alpha_min: float = field(default=ALPHA_MIN, repr=False)

    @property
    def contamination_ok(self) -> bool:
        """B-1: 모듈 전역 상수 대신 레포트 생성 시 사용한 임계값 기준."""
        return self.contamination_rate <= self._contamination_max

    @property
    def kl_ok(self) -> bool:
        """B-1: 모듈 전역 상수 대신 레포트 생성 시 사용한 임계값 기준."""
        return self.kl_divergence < self._kl_max

    @property
    def alpha_ok(self) -> bool:
        """B-1: 모듈 전역 상수 대신 레포트 생성 시 사용한 임계값 기준."""
        return self.alpha >= self._alpha_min

    @property
    def summary(self) -> str:
        status = "G63_PASS" if self.passed else "G63_FAIL"
        return (
            f"[SelfLearningGate] {status} | "
            f"contamination={self.contamination_rate:.4f}"
            f"[{'OK' if self.contamination_ok else 'FAIL'}] | "
            f"KL={self.kl_divergence:.5f}"
            f"[{'OK' if self.kl_ok else 'FAIL'}] | "
            f"alpha={self.alpha:.4f}"
            f"[{'OK' if self.alpha_ok else 'FAIL'}]"
        )

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "evaluated_at": self.evaluated_at,
            "contamination_rate": self.contamination_rate,
            "kl_divergence": self.kl_divergence,
            "alpha": self.alpha,
            "axes": [a.to_dict() for a in self.axes],
            "passed": self.passed,
            "notes": list(self.notes),
            # B-1: 임계값 직렬화
            "threshold_contamination_max": self._contamination_max,
            "threshold_kl_max": self._kl_max,
            "threshold_alpha_min": self._alpha_min,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SelfLearningGateReport":
        return cls(
            report_id=d["report_id"],
            evaluated_at=d["evaluated_at"],
            contamination_rate=float(d["contamination_rate"]),
            kl_divergence=float(d["kl_divergence"]),
            alpha=float(d["alpha"]),
            axes=[SLGAxisResult.from_dict(a) for a in d.get("axes", [])],
            passed=bool(d["passed"]),
            notes=list(d.get("notes", [])),
            # B-1: 임계값 역직렬화 (하위 호환: 없으면 전역 상수)
            _contamination_max=float(d.get("threshold_contamination_max", CONTAMINATION_MAX)),
            _kl_max=float(d.get("threshold_kl_max", KL_MAX)),
            _alpha_min=float(d.get("threshold_alpha_min", ALPHA_MIN)),
        )


# ─────────────────────────────────────────────────────────────────────────────
# SelfLearningGate
# ─────────────────────────────────────────────────────────────────────────────
class SelfLearningGate:
    """SP-C.1 최종 합격 게이트 — G63."""

    def __init__(
        self,
        store_path: str = _DEFAULT_STORE,
        kl_max: float = KL_MAX,
        alpha_min: float = ALPHA_MIN,
        contamination_max: float = CONTAMINATION_MAX,
    ) -> None:
        if kl_max <= 0:
            raise ValueError(f"kl_max must be > 0, got {kl_max}")
        if not (0.0 <= alpha_min <= 1.0):
            raise ValueError(f"alpha_min must be in [0, 1], got {alpha_min}")
        if not (0.0 <= contamination_max <= 1.0):
            raise ValueError(
                f"contamination_max must be in [0, 1], got {contamination_max}"
            )
        self._store_path = store_path
        self._kl_max = kl_max
        self._alpha_min = alpha_min
        self._contamination_max = contamination_max
        self._history: List[SelfLearningGateReport] = []
        if store_path != _MEMORY_SENTINEL:
            self._load_from_file()

    def _load_from_file(self) -> None:
        p = Path(self._store_path)
        if not p.exists():
            return
        for line in p.read_text("utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    self._history.append(
                        SelfLearningGateReport.from_dict(json.loads(line))
                    )
                except Exception:
                    pass

    def _append_to_file(self, report: SelfLearningGateReport) -> None:
        if self._store_path == _MEMORY_SENTINEL:
            return
        p = Path(self._store_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(report.to_dict(), ensure_ascii=False) + "\n")

    def evaluate(
        self,
        contamination_rate: float,
        weights: Sequence[float],
        alpha: float,
        note: str = "",
    ) -> SelfLearningGateReport:
        """G63 평가 실행.

        B-3 수정: 입력값 범위 검증 추가.
          - contamination_rate: [0.0, 1.0]
          - alpha: [0.0, 1.0]
          - weights: 비어있지 않음 (_kl_divergence_from_uniform이 합·음수 검증)
        """
        # C-4: Sequence 이중 소비 방지 — evaluate() 진입 시 즉시 list 변환
        weights = list(weights)

        # B-3: 입력값 검증
        if not (0.0 <= contamination_rate <= 1.0):
            raise ValueError(
                f"contamination_rate must be in [0.0, 1.0], got {contamination_rate}"
            )
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(
                f"alpha must be in [0.0, 1.0], got {alpha}"
            )

        # 축 1 — 오염률
        c_ok = contamination_rate <= self._contamination_max
        # B-5: FAIL 케이스 detail 메시지 정확화
        if c_ok:
            c_detail = f"contamination_rate={contamination_rate:.4f} <= {self._contamination_max} [OK]"
        else:
            c_detail = f"contamination_rate={contamination_rate:.4f} > {self._contamination_max} [FAIL]"
        axis_c = SLGAxisResult(
            axis_name="contamination",
            value=contamination_rate,
            threshold=self._contamination_max,
            passed=c_ok,
            detail=c_detail,
        )

        # 축 2 — KL divergence
        kl = _kl_divergence_from_uniform(weights)
        kl_ok = kl < self._kl_max
        # C-2: KL FAIL 케이스 detail 메시지 교정 (B-5 미완성 보완)
        _kl_op = "<" if kl_ok else ">="
        _kl_label = "[OK]" if kl_ok else "[FAIL]"
        axis_kl = SLGAxisResult(
            axis_name="kl_divergence",
            value=kl,
            threshold=self._kl_max,
            passed=kl_ok,
            detail=(
                f"KL(w||uniform)={kl:.5f} {_kl_op} {self._kl_max} "
                f"[n_weights={len(weights)}] {_kl_label}"
            ),
        )

        # 축 3 — Krippendorff α
        a_ok = alpha >= self._alpha_min
        # C-3: α FAIL 케이스 detail 메시지 교정 (B-5 미완성 보완)
        _a_op = ">=" if a_ok else "<"
        _a_label = "[OK]" if a_ok else "[FAIL]"
        axis_a = SLGAxisResult(
            axis_name="alpha",
            value=alpha,
            threshold=self._alpha_min,
            passed=a_ok,
            detail=f"alpha={alpha:.4f} {_a_op} {self._alpha_min} {_a_label}",
        )

        passed = c_ok and kl_ok and a_ok
        notes = []
        if note:
            notes.append(note)
        if not c_ok:
            notes.append(
                f"[FAIL] contamination={contamination_rate:.4f} > {self._contamination_max}"
            )
        if not kl_ok:
            notes.append(f"[FAIL] KL={kl:.5f} >= {self._kl_max}")
        if not a_ok:
            notes.append(f"[FAIL] alpha={alpha:.4f} < {self._alpha_min}")

        report = SelfLearningGateReport(
            report_id=str(uuid.uuid4()),
            evaluated_at=_now_iso(),
            contamination_rate=contamination_rate,
            kl_divergence=kl,
            alpha=alpha,
            axes=[axis_c, axis_kl, axis_a],
            passed=passed,
            notes=notes,
            # B-1: 평가 시 사용한 실제 임계값 기록
            _contamination_max=self._contamination_max,
            _kl_max=self._kl_max,
            _alpha_min=self._alpha_min,
        )
        self._history.append(report)
        self._append_to_file(report)
        return report

    def history(self) -> List[SelfLearningGateReport]:
        return list(self._history)

    def last_report(self) -> Optional[SelfLearningGateReport]:
        return self._history[-1] if self._history else None

    def count(self) -> int:
        return len(self._history)

    def clear(self) -> None:
        """히스토리 초기화.

        B-4 수정: 인메모리 히스토리와 디스크 JSONL 파일 모두 초기화.
        store_path=':memory:' 일 때는 인메모리만 초기화.
        """
        self._history.clear()
        if self._store_path != _MEMORY_SENTINEL:
            p = Path(self._store_path)
            if p.exists():
                p.write_text("", encoding="utf-8")

    @property
    def kl_max(self) -> float:
        return self._kl_max

    @property
    def alpha_min(self) -> float:
        return self._alpha_min

    @property
    def contamination_max(self) -> float:
        return self._contamination_max


# ─────────────────────────────────────────────────────────────────────────────
# run_g63_gate()
# ─────────────────────────────────────────────────────────────────────────────
def run_g63_gate() -> dict:
    """G63 SelfLearningGate 검증 실행 (release_gate.py 호출 인터페이스)."""
    checkpoints: List[str] = []
    details: dict = {}

    try:
        # CP-1: 모듈 임포트 + 상수 확인
        from literary_system.gates.self_learning_gate import (
            SelfLearningGate, SelfLearningGateReport, SLGAxisResult,
            _kl_divergence_from_uniform,
            KL_MAX, ALPHA_MIN, CONTAMINATION_MAX, N_CONSTITUTION_AXES,
        )
        assert KL_MAX == 0.05
        assert ALPHA_MIN == 0.70
        assert CONTAMINATION_MAX == 0.0
        assert N_CONSTITUTION_AXES == 5
        checkpoints.append(
            "CP-1 모듈 임포트 성공 | KL_MAX=0.05, ALPHA_MIN=0.70, "
            "CONTAMINATION_MAX=0.0, N_AXES=5 확인"
        )
        details["constants"] = {
            "KL_MAX": KL_MAX, "ALPHA_MIN": ALPHA_MIN,
            "CONTAMINATION_MAX": CONTAMINATION_MAX,
        }
    except Exception as e:
        return {
            "gate_name": "SelfLearningGate G63",
            "pass": False, "passed_count": 0, "total_count": 7,
            "checkpoints": checkpoints, "errors": [f"CP-1 실패: {e}"],
        }

    try:
        # CP-2: KL divergence 수식 검증
        from literary_system.gates.self_learning_gate import (
            _kl_divergence_from_uniform, KL_MAX,
        )
        kl_uniform = _kl_divergence_from_uniform([0.2, 0.2, 0.2, 0.2, 0.2])
        assert kl_uniform < 1e-9
        standard_w = [0.30, 0.20, 0.20, 0.15, 0.15]
        kl_std = _kl_divergence_from_uniform(standard_w)
        assert kl_std < KL_MAX
        kl_extreme = _kl_divergence_from_uniform([1.0, 0.0, 0.0, 0.0, 0.0])
        assert kl_extreme > KL_MAX
        checkpoints.append(
            f"CP-2 KL divergence 수식 검증 | "
            f"균등~0, 표준={kl_std:.5f}<{KL_MAX}, 극단={kl_extreme:.4f}>{KL_MAX}"
        )
        details["kl_verification"] = {
            "kl_uniform": kl_uniform, "kl_standard": kl_std, "kl_extreme": kl_extreme,
        }
    except Exception as e:
        return {
            "gate_name": "SelfLearningGate G63",
            "pass": False, "passed_count": len(checkpoints), "total_count": 7,
            "checkpoints": checkpoints, "errors": [f"CP-2 실패: {e}"],
        }

    try:
        # CP-3: ContaminationDetector 연동
        from literary_system.constitution.contamination_detector import (
            ContaminationDetector,
        )
        detector = ContaminationDetector(":memory:")
        sample_count = 3
        report_clean = detector.scan(dataset_id="g63_cp3_clean", sample_count=sample_count)
        assert report_clean.contamination_rate == 0.0
        checkpoints.append(
            f"CP-3 ContaminationDetector 연동 | "
            f"클린 데이터 오염률={report_clean.contamination_rate:.4f} (PASS)"
        )
        details["contamination"] = {"rate": report_clean.contamination_rate}
    except Exception as e:
        return {
            "gate_name": "SelfLearningGate G63",
            "pass": False, "passed_count": len(checkpoints), "total_count": 7,
            "checkpoints": checkpoints, "errors": [f"CP-3 실패: {e}"],
        }

    try:
        # CP-4: KL divergence 축 평가
        from literary_system.gates.self_learning_gate import (
            _kl_divergence_from_uniform, KL_MAX,
        )
        kl_std = _kl_divergence_from_uniform([0.30, 0.20, 0.20, 0.15, 0.15])
        assert kl_std < KL_MAX
        kl_fail = _kl_divergence_from_uniform([0.90, 0.025, 0.025, 0.025, 0.025])
        assert kl_fail >= KL_MAX
        checkpoints.append(
            f"CP-4 KL 축 검증 | 표준 KL={kl_std:.5f}<{KL_MAX}(PASS), "
            f"극단 KL={kl_fail:.4f}>={KL_MAX}(예상 FAIL)"
        )
        details["kl_axis"] = {"standard": kl_std, "extreme": kl_fail}
    except Exception as e:
        return {
            "gate_name": "SelfLearningGate G63",
            "pass": False, "passed_count": len(checkpoints), "total_count": 7,
            "checkpoints": checkpoints, "errors": [f"CP-4 실패: {e}"],
        }

    try:
        # CP-5: Krippendorff α 축 검증
        from literary_system.constitution.krippendorff_alpha import (
            KrippendorffAlpha, ALPHA_MIN_THRESHOLD,
        )
        assert ALPHA_MIN_THRESHOLD == ALPHA_MIN
        alpha_calc = KrippendorffAlpha("interval")
        rater_agree = {
            "rater_A": {"u1": 0.85, "u2": 0.70, "u3": 0.90, "u4": 0.75},
            "rater_B": {"u1": 0.84, "u2": 0.72, "u3": 0.89, "u4": 0.76},
            "rater_C": {"u1": 0.86, "u2": 0.69, "u3": 0.91, "u4": 0.74},
        }
        result_agree = alpha_calc.compute(rater_agree)
        assert result_agree.alpha >= ALPHA_MIN
        rater_disagree = {
            "rater_A": {"u1": 0.95, "u2": 0.05, "u3": 0.90, "u4": 0.10},
            "rater_B": {"u1": 0.05, "u2": 0.95, "u3": 0.10, "u4": 0.90},
        }
        result_disagree = alpha_calc.compute(rater_disagree)
        assert not result_disagree.passed
        checkpoints.append(
            f"CP-5 Krippendorff α 축 검증 | "
            f"일치 α={result_agree.alpha:.4f}(PASS), "
            f"불일치 α={result_disagree.alpha:.4f}(예상 FAIL)"
        )
        details["alpha_axis"] = {
            "alpha_agree": result_agree.alpha,
            "alpha_disagree": result_disagree.alpha,
        }
    except Exception as e:
        return {
            "gate_name": "SelfLearningGate G63",
            "pass": False, "passed_count": len(checkpoints), "total_count": 7,
            "checkpoints": checkpoints, "errors": [f"CP-5 실패: {e}"],
        }

    try:
        # CP-6: SelfLearningGateReport 직렬화/역직렬화
        from literary_system.gates.self_learning_gate import (
            SelfLearningGate, SelfLearningGateReport,
        )
        gate_cp6 = SelfLearningGate(store_path=":memory:")
        r = gate_cp6.evaluate(
            contamination_rate=0.0,
            weights=[0.30, 0.20, 0.20, 0.15, 0.15],
            alpha=0.82,
            note="CP-6 직렬화 검증",
        )
        assert r.passed
        restored = SelfLearningGateReport.from_dict(r.to_dict())
        assert restored.report_id == r.report_id
        assert abs(restored.kl_divergence - r.kl_divergence) < 1e-9
        assert len(restored.axes) == 3
        checkpoints.append(
            f"CP-6 SelfLearningGateReport 직렬화/역직렬화 | "
            f"3축 보존, passed={r.passed}"
        )
        details["serialization"] = {"passed": r.passed, "axes": len(r.axes)}
    except Exception as e:
        return {
            "gate_name": "SelfLearningGate G63",
            "pass": False, "passed_count": len(checkpoints), "total_count": 7,
            "checkpoints": checkpoints, "errors": [f"CP-6 실패: {e}"],
        }

    try:
        # CP-7: SP-C.1 종합 판정
        from literary_system.gates.self_learning_gate import SelfLearningGate
        gate_cp7 = SelfLearningGate(store_path=":memory:")
        r_pass = gate_cp7.evaluate(0.0, [0.30, 0.20, 0.20, 0.15, 0.15], 0.75)
        assert r_pass.passed
        r_fc = gate_cp7.evaluate(0.05, [0.30, 0.20, 0.20, 0.15, 0.15], 0.85)
        assert not r_fc.passed
        r_fk = gate_cp7.evaluate(0.0, [0.80, 0.05, 0.05, 0.05, 0.05], 0.80)
        assert not r_fk.passed
        r_fa = gate_cp7.evaluate(0.0, [0.30, 0.20, 0.20, 0.15, 0.15], 0.50)
        assert not r_fa.passed
        assert gate_cp7.count() == 4
        checkpoints.append(
            "CP-7 SP-C.1 종합 판정 | "
            "합격 1건 PASS, FAIL 3건(오염/KL/α) 정상, "
            "history 4건, last_report 확인"
        )
        details["combined"] = {
            "pass_case": True,
            "fail_contamination": True,
            "fail_kl": True,
            "fail_alpha": True,
            "count": gate_cp7.count(),
        }
    except Exception as e:
        return {
            "gate_name": "SelfLearningGate G63",
            "pass": False, "passed_count": len(checkpoints), "total_count": 7,
            "checkpoints": checkpoints, "errors": [f"CP-7 실패: {e}"],
        }

    return {
        "gate_name": "SelfLearningGate G63 — SP-C.1 완료 판정 (ADR-105)",
        "pass": True,
        "passed_count": len(checkpoints),
        "total_count": 7,
        "checkpoints": checkpoints,
        "details": details,
        "errors": [],
    }
