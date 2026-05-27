"""PublicSDK — 커스텀 예외 계층 (ADR-116)."""
from __future__ import annotations


class LiteraryOSError(Exception):
    """Literary OS SDK 기본 예외."""

    def __init__(self, message: str, code: str = "UNKNOWN") -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


class SDKConfigError(LiteraryOSError):
    """SDK 설정 오류."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="SDK_CONFIG_ERROR")


class AnalyzeError(LiteraryOSError):
    """analyze() 실행 중 발생하는 오류."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="ANALYZE_ERROR")


class RepairError(LiteraryOSError):
    """repair() 실행 중 발생하는 오류."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="REPAIR_ERROR")


class PredictError(LiteraryOSError):
    """predict() 실행 중 발생하는 오류."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="PREDICT_ERROR")


class GenerateError(LiteraryOSError):
    """generate() 실행 중 발생하는 오류."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="GENERATE_ERROR")


class RateLimitError(LiteraryOSError):
    """RPM 초과 오류."""

    def __init__(self, limit: int) -> None:
        super().__init__(f"Rate limit exceeded: {limit} RPM", code="RATE_LIMIT_EXCEEDED")
        self.limit = limit


class ValidationError(LiteraryOSError):
    """입력 검증 실패."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"Validation failed for '{field}': {reason}", code="VALIDATION_ERROR")
        self.field = field
        self.reason = reason
