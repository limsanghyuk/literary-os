"""
V428: i18n 메시지 로더.
환경변수 LITERARY_OS_LOCALE (ko|en, 기본 ko) 에 따라 메시지 모듈 선택.
"""
from __future__ import annotations

import os
import importlib
from types import ModuleType

_SUPPORTED = ("ko", "en")
_DEFAULT   = "ko"


def _load_locale() -> ModuleType:
    locale = os.environ.get("LITERARY_OS_LOCALE", _DEFAULT).lower()
    if locale not in _SUPPORTED:
        locale = _DEFAULT
    return importlib.import_module(f"apps.studio_api.messages.{locale}")


# 현재 로케일 메시지 모듈 (애플리케이션 시작 시 1회 로드)
_msg: ModuleType = _load_locale()


def get(key: str, default: str = "") -> str:
    """메시지 키로 현재 로케일 문자열 반환."""
    return getattr(_msg, key, default)


def reload(locale: str | None = None) -> None:
    """로케일 재로드 (테스트/런타임 전환용)."""
    global _msg
    if locale:
        os.environ["LITERARY_OS_LOCALE"] = locale
    _msg = _load_locale()


# 편의 접근자 — 자주 사용되는 메시지
def cb_gate_open()     -> str: return get("CB_GATE_OPEN")
def cb_gate_degraded() -> str: return get("CB_GATE_DEGRADED")
def hint_overload()    -> str: return get("HINT_OVERLOAD")
def hint_voice_drift() -> str: return get("HINT_VOICE_DRIFT")
def hint_payoff_debt() -> str: return get("HINT_PAYOFF_DEBT")
def hint_fatigue()     -> str: return get("HINT_FATIGUE")
def warn_no_delimiter()-> str: return get("WARN_NO_DELIMITER")
