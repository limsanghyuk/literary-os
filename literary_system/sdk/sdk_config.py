"""PublicSDK — 설정 클래스 (ADR-116)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class SDKConfig:
    """Literary OS PublicSDK 설정.

    환경변수 우선 → 생성자 인자 → 기본값 순으로 적용된다.
    """

    # 서비스 엔드포인트 (로컬 인퍼런스 게이트웨이)
    inference_endpoint: str = field(
        default_factory=lambda: os.getenv("LOS_INFERENCE_ENDPOINT", "http://localhost:8080")
    )

    # 요청 타임아웃 (초)
    timeout_sec: float = field(
        default_factory=lambda: float(os.getenv("LOS_SDK_TIMEOUT", "30"))
    )

    # 분당 최대 요청 수 (0 = 무제한)
    max_rpm: int = field(
        default_factory=lambda: int(os.getenv("LOS_SDK_MAX_RPM", "1000"))
    )

    # 오프라인 모드 — 실제 인퍼런스 없이 stub 응답 반환
    offline_mode: bool = field(
        default_factory=lambda: os.getenv("LOS_SDK_OFFLINE", "true").lower() == "true"
    )

    # AutoPromotionGate(G62)를 통과한 모델만 서빙 (LLM-1 원칙)
    require_promoted_model: bool = True

    # 기본 언어
    default_lang: str = "ko"

    # 분석 품질 합격선
    quality_threshold: float = 0.65

    def __post_init__(self) -> None:
        if self.timeout_sec <= 0:
            raise ValueError("timeout_sec must be positive")
        if self.max_rpm < 0:
            raise ValueError("max_rpm must be >= 0")
        if not (0.0 <= self.quality_threshold <= 1.0):
            raise ValueError("quality_threshold must be in [0, 1]")

    @classmethod
    def from_env(cls) -> "SDKConfig":
        """환경변수에서 설정을 읽어 인스턴스를 생성한다."""
        return cls()

    def to_dict(self) -> dict:
        """설정을 딕셔너리로 직렬화한다."""
        return {
            "inference_endpoint": self.inference_endpoint,
            "timeout_sec": self.timeout_sec,
            "max_rpm": self.max_rpm,
            "offline_mode": self.offline_mode,
            "require_promoted_model": self.require_promoted_model,
            "default_lang": self.default_lang,
            "quality_threshold": self.quality_threshold,
        }
