from __future__ import annotations


class LiterarySystemError(Exception):
    """Base error."""


class SchemaValidationError(LiterarySystemError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class AuthorityError(LiterarySystemError):
    pass


class PromotionError(LiterarySystemError):
    pass
