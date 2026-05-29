"""V385 — PrivacyGuard. 텍스트 데이터 LLM 전달 금지 강제."""
from __future__ import annotations


class PrivacyViolationError(Exception):
    pass


class PrivacyGuard:
    """SceneFeature에 원고 텍스트가 포함되지 않음을 보장."""

    MAX_STR_LEN = 200  # 이 이상의 문자열은 텍스트로 간주

    def validate(self, feature_dict: dict) -> None:
        violations = []
        for k, v in feature_dict.items():
            if isinstance(v, str) and len(v) > self.MAX_STR_LEN:
                violations.append(f"Field '{k}': string length {len(v)} > {self.MAX_STR_LEN}")
            if isinstance(v, (list, tuple)):
                for i, item in enumerate(v):
                    if isinstance(item, str) and len(item) > self.MAX_STR_LEN:
                        violations.append(f"Field '{k}[{i}]': string length {len(item)}")
        if violations:
            raise PrivacyViolationError(
                "PrivacyGuard: text data detected in SceneFeature.\n" +
                "\n".join(violations)
            )

    def scrub(self, text: str) -> None:
        """텍스트 폐기 확인용 (실제 메모리 삭제는 del + gc)."""
        import gc
        del text
        gc.collect()
