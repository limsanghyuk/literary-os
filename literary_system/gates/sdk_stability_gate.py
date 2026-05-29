"""literary_system/gates/sdk_stability_gate.py

Gate G70 — SDKStabilityGate (ADR-123)

베타 SDK 안정성 게이트.

합격 조건:
  1. P0 버그 0건 (크래시 / 예외 미처리 / 데이터 손실)
  2. 베타 사용자 N명 × SDK 4메서드 전체 호출 성공률 100%
  3. 평균 응답 시간 ≤ SLO_LATENCY_MS
  4. SDK 버전 정합성 (VERSION 필드 존재 및 semver 형식)
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from literary_system.sdk.public_sdk import LiteraryOSClient
from literary_system.sdk.sdk_config import SDKConfig

__all__ = [
    "SDKStabilityGate",
    "BetaUserResult",
    "StabilityReport",
    "run_g70",
    "SDKStabilityError",
]

# ── 상수 ──────────────────────────────────────────────────────────────
BETA_USER_COUNT: int = 20           # 베타 사용자 수
MAX_P0_BUGS: int = 0                # 허용 P0 버그 건수
SLO_LATENCY_MS: float = 5000.0     # 평균 응답 시간 SLO (ms)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")
_GATE_ID = "G70"

# ── 예외 ──────────────────────────────────────────────────────────────

class SDKStabilityError(RuntimeError):
    """G70 게이트 런타임 오류."""


# ── 데이터 클래스 ─────────────────────────────────────────────────────

@dataclass
class BetaUserResult:
    """단일 베타 사용자 SDK 호출 결과."""
    user_id: str
    analyze_ok: bool
    repair_ok: bool
    predict_ok: bool
    generate_ok: bool
    analyze_ms: float
    repair_ms: float
    predict_ms: float
    generate_ms: float
    p0_errors: list[str] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return (self.analyze_ok and self.repair_ok
                and self.predict_ok and self.generate_ok)

    @property
    def total_ms(self) -> float:
        return self.analyze_ms + self.repair_ms + self.predict_ms + self.generate_ms

    @property
    def avg_ms(self) -> float:
        return self.total_ms / 4.0


@dataclass
class StabilityReport:
    """G70 게이트 전체 리포트."""
    gate_id: str = _GATE_ID
    gate_name: str = "SDKStabilityGate"
    passed: bool = False
    beta_users: int = 0
    success_users: int = 0
    p0_count: int = 0
    avg_latency_ms: float = 0.0
    slo_latency_ms: float = SLO_LATENCY_MS
    sdk_version: str = ""
    version_valid: bool = False
    errors: list[str] = field(default_factory=list)
    user_results: list[BetaUserResult] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "passed": self.passed,
            "beta_users": self.beta_users,
            "success_users": self.success_users,
            "p0_count": self.p0_count,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "slo_latency_ms": self.slo_latency_ms,
            "sdk_version": self.sdk_version,
            "version_valid": self.version_valid,
            "errors": self.errors,
            "summary": self.summary,
        }


# ── 베타 시나리오 데이터 ──────────────────────────────────────────────

_BETA_TEXTS = [
    "소나기는 갑자기 쏟아졌다. 지붕 위 빗소리가 요란했다.",
    "그는 창밖을 바라보며 오래된 기억을 떠올렸다.",
    "두 사람은 말없이 식탁 앞에 마주 앉았다.",
    "바람이 불어와 빈 페이지를 넘겼다.",
    "도서관의 조용한 오후, 그녀는 책 속에서 길을 잃었다.",
]

_BETA_CONTEXTS = [
    "현대 한국 소설 — 일상적인 감정 묘사",
    "서울 배경 로맨스 — 주인공 두 명",
    "가족 드라마 — 중산층 가정",
    "청춘 소설 — 20대 주인공",
    "역사 소설 — 조선시대 배경",
]


# ── 게이트 ────────────────────────────────────────────────────────────

class SDKStabilityGate:
    """G70: PublicSDK 베타 안정성 게이트."""

    def __init__(
        self,
        beta_user_count: int = BETA_USER_COUNT,
        slo_ms: float = SLO_LATENCY_MS,
        client: LiteraryOSClient | None = None,
    ) -> None:
        self._n = max(1, beta_user_count)
        self._slo = slo_ms
        self._client = client or LiteraryOSClient(
            config=SDKConfig(offline_mode=True, max_rpm=1000)
        )

    def run(self) -> StabilityReport:
        report = StabilityReport(beta_users=self._n, slo_latency_ms=self._slo)

        # 1. SDK 버전 확인
        try:
            from literary_system.sdk import __version__ as sdk_ver
            report.sdk_version = sdk_ver
        except ImportError:
            try:
                report.sdk_version = self._client.stats().get("sdk_version", "unknown")
            except Exception:
                report.sdk_version = "unknown"

        report.version_valid = bool(SEMVER_RE.match(report.sdk_version))

        # 2. 베타 사용자 시뮬레이션
        total_latency: float = 0.0
        for i in range(self._n):
            result = self._simulate_user(f"beta_user_{i:03d}", i)
            report.user_results.append(result)
            if result.all_ok:
                report.success_users += 1
            else:
                report.p0_count += len(result.p0_errors)
                report.errors.extend(result.p0_errors)
            total_latency += result.avg_ms

        report.avg_latency_ms = total_latency / self._n if self._n > 0 else 0.0

        # 3. 합격 판정
        report.passed = (
            report.p0_count == MAX_P0_BUGS
            and report.success_users == self._n
            and report.avg_latency_ms <= self._slo
            and report.version_valid
        )
        status = "PASS" if report.passed else "FAIL"
        report.summary = (
            f"G70 {status}: {report.success_users}/{report.beta_users} 사용자 성공, "
            f"P0={report.p0_count}, avg_ms={report.avg_latency_ms:.1f}"
        )
        return report

    def _simulate_user(self, user_id: str, idx: int) -> BetaUserResult:
        """단일 베타 사용자 — SDK 4메서드 순차 호출."""
        text = _BETA_TEXTS[idx % len(_BETA_TEXTS)]
        ctx = _BETA_CONTEXTS[idx % len(_BETA_CONTEXTS)]
        p0_errors: list[str] = []

        # analyze
        t0 = time.monotonic()
        try:
            result = self._client.analyze(text=text, context=ctx)
            analyze_ok = result is not None
            if not analyze_ok:
                p0_errors.append(f"{user_id}: analyze returned None")
        except Exception as exc:
            analyze_ok = False
            p0_errors.append(f"{user_id}: analyze crash — {exc}")
        analyze_ms = (time.monotonic() - t0) * 1000.0

        # repair
        t0 = time.monotonic()
        try:
            result = self._client.repair(text=text, issues=["문장 리듬 개선"])
            repair_ok = result is not None
            if not repair_ok:
                p0_errors.append(f"{user_id}: repair returned None")
        except Exception as exc:
            repair_ok = False
            p0_errors.append(f"{user_id}: repair crash — {exc}")
        repair_ms = (time.monotonic() - t0) * 1000.0

        # predict
        t0 = time.monotonic()
        try:
            result = self._client.predict(context=ctx, n=3)
            predict_ok = result is not None
            if not predict_ok:
                p0_errors.append(f"{user_id}: predict returned None")
        except Exception as exc:
            predict_ok = False
            p0_errors.append(f"{user_id}: predict crash — {exc}")
        predict_ms = (time.monotonic() - t0) * 1000.0

        # generate
        t0 = time.monotonic()
        try:
            result = self._client.generate(
                title="봄의 끝", characters=["지수", "민준"],
                setting="서울 카페", conflict="이별 직전의 대화"
            )
            generate_ok = result is not None
            if not generate_ok:
                p0_errors.append(f"{user_id}: generate returned None")
        except Exception as exc:
            generate_ok = False
            p0_errors.append(f"{user_id}: generate crash — {exc}")
        generate_ms = (time.monotonic() - t0) * 1000.0

        return BetaUserResult(
            user_id=user_id,
            analyze_ok=analyze_ok,
            repair_ok=repair_ok,
            predict_ok=predict_ok,
            generate_ok=generate_ok,
            analyze_ms=analyze_ms,
            repair_ms=repair_ms,
            predict_ms=predict_ms,
            generate_ms=generate_ms,
            p0_errors=p0_errors,
        )


def run_g70(
    beta_user_count: int = BETA_USER_COUNT,
    client: LiteraryOSClient | None = None,
) -> dict[str, Any]:
    """G70 게이트 실행 진입점."""
    gate = SDKStabilityGate(beta_user_count=beta_user_count, client=client)
    return gate.run().to_dict()
