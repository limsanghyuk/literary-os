"""
V325 - EmbeddingEncoder  (Phase 2)
numpy 전용 TF-IDF 벡터화기.

설계 원칙 (P3 추가 패키지 0개):
  - numpy만 사용 (scikit-learn, torch 불필요)
  - fit(corpus) → 어휘 사전 + IDF 벡터 구축
  - transform(texts) → TF-IDF 행렬 반환
  - SimpleVectorRetriever가 내부적으로 사용
  - sentence-transformers 교체 가능 인터페이스 준수
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import math
import re
from typing import Any

import numpy as np

# ────────────────────────────────────────────────────────────────
# 토크나이저
# ────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """
    텍스트 → 소문자 토큰 리스트.
    한국어 음절 + 영문 단어 모두 지원.
    """
    text = text.lower()
    # 한국어·영문·숫자 토큰 추출 (구두점·공백 제거)
    tokens = re.findall(r"[가-힣]+|[a-z0-9]+", text)
    return [t for t in tokens if len(t) >= 2]   # 1글자 불용어 제거


# ────────────────────────────────────────────────────────────────
# EmbeddingEncoder
# ────────────────────────────────────────────────────────────────

class EmbeddingEncoder:
    """
    numpy 전용 TF-IDF 벡터화기.

    사용 예:
        enc = EmbeddingEncoder()
        matrix = enc.fit_transform(["고애신이 교회에 갔다", "유진 초이가 따라갔다"])
        vec    = enc.transform(["고애신"])
    """

    def __init__(self, max_features: int = 5000, min_df: int = 1) -> None:
        """
        Args:
            max_features: 최대 어휘 크기 (IDF 내림차순 상위 N)
            min_df:       최소 문서 빈도 (너무 희귀한 단어 제외)
        """
        self.max_features = max_features
        self.min_df       = min_df

        self.vocabulary_: dict[str, int] = {}   # 단어 → 컬럼 인덱스
        self.idf_: np.ndarray | None = None     # IDF 벡터
        self._fitted: bool = False

    # ── 공개 API ─────────────────────────────────────────────────

    def fit(self, corpus: list[str]) -> "EmbeddingEncoder":
        """
        코퍼스로 어휘 사전 + IDF 구축.

        Args:
            corpus: 문자열 리스트

        Returns:
            self (체이닝 가능)
        """
        if not corpus:
            self.vocabulary_ = {}
            self.idf_ = np.array([], dtype=np.float32)
            self._fitted = True
            return self

        n_docs = len(corpus)
        tokenized = [_tokenize(doc) for doc in corpus]

        # 문서 빈도(df) 계산
        df: dict[str, int] = {}
        for tokens in tokenized:
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        # min_df 필터링
        vocab_list = [w for w, cnt in df.items() if cnt >= self.min_df]

        # IDF = log((1+N)/(1+df)) + 1  (sklearn 방식, 분모 0 방지)
        idf_values: list[float] = []
        for w in vocab_list:
            idf_values.append(math.log((1 + n_docs) / (1 + df[w])) + 1.0)

        # max_features 제한: IDF 내림차순 상위 N
        if len(vocab_list) > self.max_features:
            pairs = sorted(zip(idf_values, vocab_list), reverse=True)
            pairs = pairs[: self.max_features]
            idf_values = [p[0] for p in pairs]
            vocab_list = [p[1] for p in pairs]

        self.vocabulary_ = {w: i for i, w in enumerate(vocab_list)}
        self.idf_ = np.array(idf_values, dtype=np.float32)
        self._fitted = True
        return self

    def transform(self, texts: list[str]) -> np.ndarray:
        """
        fit()된 어휘로 텍스트 목록 → TF-IDF 행렬.

        Args:
            texts: 문자열 리스트 (n_docs,)

        Returns:
            np.ndarray shape (n_docs, vocab_size)  float32
        """
        if not self._fitted:
            raise RuntimeError("EmbeddingEncoder.fit()을 먼저 호출하세요.")
        if not self.vocabulary_:
            return np.zeros((len(texts), 0), dtype=np.float32)

        n = len(texts)
        vocab_size = len(self.vocabulary_)
        matrix = np.zeros((n, vocab_size), dtype=np.float32)

        for i, text in enumerate(texts):
            tokens = _tokenize(text)
            if not tokens:
                continue
            tf: dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            # 정규화 TF = count / total_tokens
            total = len(tokens)
            for word, cnt in tf.items():
                if word in self.vocabulary_:
                    col = self.vocabulary_[word]
                    matrix[i, col] = (cnt / total) * self.idf_[col]

        # L2 정규화 (코사인 유사도 계산을 위해)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        matrix /= norms

        return matrix

    def fit_transform(self, corpus: list[str]) -> np.ndarray:
        """fit() + transform() 통합."""
        return self.fit(corpus).transform(corpus)

    # ── 상태 조회 ────────────────────────────────────────────────

    @property
    def vocab_size(self) -> int:
        return len(self.vocabulary_)

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def get_feature_names(self) -> list[str]:
        """어휘 목록 반환 (인덱스 순)."""
        return [w for w, _ in sorted(self.vocabulary_.items(), key=lambda x: x[1])]
