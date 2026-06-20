"""learning/pairing/tokenizer.py — I5 토크나이저 잠금.

단일 토크나이저를 주입하고 그 정체성을 tokenizer_sha로 동결한다. 실 학습에서는
모델 토크나이저(HF)를 어댑터로 감싸 주입하고, 본 빌더는 토큰 수만 소비한다.
"""
from __future__ import annotations
import hashlib
from typing import List, Protocol, runtime_checkable


@runtime_checkable
class Tokenizer(Protocol):
    identity: str
    def tokenize(self, text: str) -> List[str]: ...


def tokenizer_sha(tok: Tokenizer) -> str:
    """토크나이저 정체성 문자열의 sha256(앞 16자). ledger·report에 동결 기록."""
    return hashlib.sha256(tok.identity.encode("utf-8")).hexdigest()[:16]


class WhitespaceTokenizer:
    """테스트·기본용 결정론 토크나이저. 실 학습에선 모델 토크나이저로 교체."""
    identity = "whitespace-v1"

    def tokenize(self, text: str) -> List[str]:
        return text.split()
