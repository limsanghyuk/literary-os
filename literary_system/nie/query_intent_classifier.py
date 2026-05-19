"""
V509~V510 - QueryIntentClassifier + DramaLexicon
NIL Step 6: 쿼리 의도 분류 → HybridRetriever 가중치 동적 조정.

설계:
  3-type: CHARACTER / EMOTIONAL / PLOT_EVENT
  CHARACTER:  pn_ratio > 0.40 → BM25=0.70, k=40
  EMOTIONAL:  emotion_ratio > 0.35 → BM25=0.30, k=60
  PLOT_EVENT: else → BM25=0.50, k=50

DramaLexicon BM25 부스팅:
  CHARACTER_NAMES × 1.5
  EPISODE_TERMS  × 1.3
  DRAMA_KW       × 1.2
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    CHARACTER  = "CHARACTER"
    EMOTIONAL  = "EMOTIONAL"
    PLOT_EVENT = "PLOT_EVENT"


@dataclass
class ClassifierResult:
    intent: QueryIntent
    bm25_weight: float
    dense_weight: float
    top_k: int
    pn_ratio: float
    emotion_ratio: float
    confidence: float

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.value,
            "bm25_weight": round(self.bm25_weight, 3),
            "dense_weight": round(self.dense_weight, 3),
            "top_k": self.top_k,
            "pn_ratio": round(self.pn_ratio, 3),
            "emotion_ratio": round(self.emotion_ratio, 3),
            "confidence": round(self.confidence, 3),
        }


# ── DramaLexicon ──────────────────────────────────────────────────

class DramaLexicon:
    """
    한국 드라마 도메인 BM25 부스팅 사전.
    CHARACTER_NAMES × 1.5 / EPISODE_TERMS × 1.3 / DRAMA_KW × 1.2
    """

    BOOST_CHARACTER = 1.5
    BOOST_EPISODE   = 1.3
    BOOST_DRAMA_KW  = 1.2

    # 기본 드라마 키워드 (런타임에 character_ids로 보강)
    _EMOTION_KW: Set[str] = {
        "눈물", "슬픔", "분노", "기쁨", "공포", "불안", "사랑", "증오",
        "질투", "원망", "그리움", "설렘", "실망", "배신", "용서", "감동",
        "tears", "grief", "anger", "joy", "fear", "anxiety", "love", "hate",
        "jealousy", "longing", "excitement", "disappointment", "betrayal",
    }

    _EPISODE_TERMS: Set[str] = {
        "화", "에피소드", "회", "episode", "ep", "방영", "시즌",
        "1화", "2화", "3화", "4화", "5화", "6화", "7화", "8화",
        "최종화", "마지막화", "특별편", "파일럿",
    }

    _DRAMA_KW: Set[str] = {
        "반전", "복선", "클리프행거", "갈등", "화해", "결말",
        "주인공", "악당", "조연", "남주", "여주", "캐릭터",
        "장면", "대사", "씬", "플롯", "스토리",
        "foreshadow", "twist", "cliffhanger", "conflict", "resolution",
        "protagonist", "antagonist", "supporting", "scene", "plot",
    }

    def __init__(self, character_names: Optional[List[str]] = None) -> None:
        self._character_names: Set[str] = set(character_names or [])

    def add_characters(self, names: List[str]) -> None:
        self._character_names.update(names)

    def boost_score(self, token: str) -> float:
        """토큰에 대한 BM25 부스팅 배수 반환."""
        t = token.lower().strip()
        if t in self._character_names or token in self._character_names:
            return self.BOOST_CHARACTER
        if t in {e.lower() for e in self._EPISODE_TERMS}:
            return self.BOOST_EPISODE
        if t in {d.lower() for d in self._DRAMA_KW}:
            return self.BOOST_DRAMA_KW
        return 1.0

    def tokenize_and_boost(self, query: str) -> Dict[str, float]:
        """쿼리 토크나이즈 + 토큰별 부스팅 배수 반환."""
        tokens = re.split(r'[\s,\.!?]+', query.lower())
        return {tok: self.boost_score(tok) for tok in tokens if tok}

    def emotion_ratio(self, query: str) -> float:
        """감정 키워드 비율 계산."""
        tokens = re.split(r'[\s,\.!?]+', query.lower())
        if not tokens:
            return 0.0
        emotion_cnt = sum(1 for t in tokens if t in {e.lower() for e in self._EMOTION_KW})
        return emotion_cnt / len(tokens)

    def character_name_ratio(self, query: str, char_ids: Optional[List[str]] = None) -> float:
        """인물명 비율 계산."""
        names = self._character_names | set(char_ids or [])
        if not names:
            return 0.0
        tokens = re.split(r'[\s,\.!?]+', query)
        if not tokens:
            return 0.0
        char_cnt = sum(1 for t in tokens if t in names or t.lower() in {n.lower() for n in names})
        return char_cnt / len(tokens)


# ── QueryIntentClassifier ─────────────────────────────────────────

class QueryIntentClassifier:
    """
    NIL Step 6 — 쿼리 의도 분류 + HybridRetriever 파라미터 결정.

    CHARACTER:  pn_ratio > PN_THRESHOLD  → BM25=0.70, k=40
    EMOTIONAL:  emotion_ratio > EM_THRESHOLD → BM25=0.30, k=60
    PLOT_EVENT: else                     → BM25=0.50, k=50
    """

    PN_THRESHOLD = 0.40
    EM_THRESHOLD = 0.35

    # (bm25_weight, dense_weight, top_k)
    _PARAMS = {
        QueryIntent.CHARACTER:  (0.70, 0.30, 40),
        QueryIntent.EMOTIONAL:  (0.30, 0.70, 60),
        QueryIntent.PLOT_EVENT: (0.50, 0.50, 50),
    }

    def __init__(
        self,
        character_ids: Optional[List[str]] = None,
        lexicon: Optional[DramaLexicon] = None,
    ) -> None:
        self._char_ids = list(character_ids or [])
        self._lexicon = lexicon or DramaLexicon(self._char_ids)

    def add_characters(self, char_ids: List[str]) -> None:
        self._char_ids.extend(char_ids)
        self._lexicon.add_characters(char_ids)

    def classify(self, query: str) -> ClassifierResult:
        """
        쿼리 의도 분류 → BM25/Dense 가중치 + top_k 반환.
        """
        pn_ratio = self._lexicon.character_name_ratio(query, self._char_ids)
        emotion_ratio = self._lexicon.emotion_ratio(query)

        # 분류 우선순위: CHARACTER > EMOTIONAL > PLOT_EVENT
        if pn_ratio > self.PN_THRESHOLD:
            intent = QueryIntent.CHARACTER
            confidence = min(1.0, pn_ratio / self.PN_THRESHOLD)
        elif emotion_ratio > self.EM_THRESHOLD:
            intent = QueryIntent.EMOTIONAL
            confidence = min(1.0, emotion_ratio / self.EM_THRESHOLD)
        else:
            intent = QueryIntent.PLOT_EVENT
            confidence = 1.0 - max(pn_ratio, emotion_ratio)

        bm25_w, dense_w, top_k = self._PARAMS[intent]
        return ClassifierResult(
            intent=intent,
            bm25_weight=bm25_w,
            dense_weight=dense_w,
            top_k=top_k,
            pn_ratio=pn_ratio,
            emotion_ratio=emotion_ratio,
            confidence=confidence,
        )

    def get_retrieval_params(self, query: str) -> dict:
        """HybridRetriever 직접 주입용 파라미터 딕셔너리."""
        result = self.classify(query)
        return {
            "bm25_weight": result.bm25_weight,
            "dense_weight": result.dense_weight,
            "top_k": result.top_k,
            "intent": result.intent.value,
        }
