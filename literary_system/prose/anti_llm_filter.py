"""V370: KoreanAntiLLMFilter — 한국 드라마 AI 클리셰 교체 필터."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────
#  기본 클리셰 사전 (장르 무관 공통 50+ 쌍)
# ──────────────────────────────────────────────────────────────────────
_BASE_DICT: Dict[str, str] = {
    # 감정 추상어
    "복잡한 감정이 밀려왔다":        "식은 숨이 한 번 새어 나왔다",
    "복잡한 감정이 밀려들었다":       "손끝이 천천히 식었다",
    "감정이 복잡했다":               "입 안이 바짝 말랐다",
    "기분이 묘했다":                 "발바닥이 땅에서 뜨는 것 같았다",
    "가슴이 먹먹했다":               "목 안쪽이 마른 종이처럼 붙었다",
    "마음이 무거웠다":               "어깨가 한 뼘쯤 낮아진 것 같았다",
    "마음이 복잡했다":               "손바닥을 두 번 폈다 접었다",
    "말로 표현할 수 없는 감정":       "이름 붙이지 않기로 한 것",
    "형용할 수 없는 감정":            "모르는 체하기로 한 것",
    # 눈물·시선
    "눈물이 핑 돌았다":              "아래 눈꺼풀이 한 번 떨렸다",
    "눈물이 왈칵 쏟아졌다":          "눈 안쪽이 뜨거워지는 게 느껴졌다",
    "눈물을 참았다":                 "턱에 힘이 들어갔다",
    "눈시울이 붉어졌다":             "코끝이 찌릿했다",
    # 운명·시간
    "운명의 장난처럼":               "기울어진 시간처럼",
    "운명이라고 느꼈다":             "이상하게 이미 알고 있던 것 같았다",
    "그 순간, 모든 것이 달라질 것만 같았다": "문틈으로 들어오던 바람이 멎었다",
    "모든 것이 변한 것 같았다":       "시계 초침이 한 박자 늦게 움직였다",
    "그 순간 시간이 멈춘 것 같았다":  "숨이 반 박자 늦게 나왔다",
    # 심장·가슴
    "심장이 두근거렸다":             "귀 뒤쪽이 달아올랐다",
    "심장이 빠르게 뛰었다":          "손끝이 찌릿했다",
    "가슴이 두근댔다":               "목 아래쪽이 조여드는 것 같았다",
    "가슴이 벅찼다":                 "갈비뼈 사이로 뭔가 차오르는 것 같았다",
    "가슴이 아팠다":                 "갈비뼈 아래가 빈 것처럼 느껴졌다",
    # 침묵·공백
    "침묵이 흘렀다":                 "바람 소리만 들렸다",
    "정적이 흘렀다":                 "냉장고 소리가 유독 크게 들렸다",
    "말문이 막혔다":                 "혀가 입천장에 붙었다",
    # 배신·충격
    "배신감이 밀려왔다":             "발밑이 빠지는 것 같았다",
    "충격이었다":                   "눈이 한 번 깜빡이지 않았다",
    "믿기지 않았다":                 "같은 문장을 세 번 읽었다",
    # 안도·기쁨
    "안도감이 밀려왔다":             "어깨가 한 박자 늦게 내려갔다",
    "긴장이 풀렸다":                 "뒷목이 천천히 식었다",
    "기쁨이 넘쳤다":                 "발걸음이 한 박자 빨라졌다",
    # 두려움·긴장
    "두려웠다":                     "등 뒤가 서늘했다",
    "무서웠다":                     "발바닥이 바닥에 들러붙는 것 같았다",
    "긴장했다":                     "손바닥이 축축해졌다",
    "불안했다":                     "눈이 자꾸 문 쪽으로 갔다",
    # 분노
    "화가 났다":                    "이를 악물었다",
    "분노가 치밀었다":               "손이 주먹을 쥐었다",
    "억울했다":                     "아랫입술을 깨물었다",
    # 부끄러움·당황
    "부끄러웠다":                   "뺨이 뜨거워졌다",
    "당황했다":                     "발끝이 안쪽으로 돌아갔다",
    "민망했다":                     "시선이 바닥으로 떨어졌다",
    # 혼란·의문
    "혼란스러웠다":                  "머릿속이 한동안 비었다",
    "이해할 수 없었다":              "눈썹이 저도 모르게 내려갔다",
    # 결심·각오
    "각오를 다졌다":                 "발에 힘을 주었다",
    "결심했다":                     "턱을 한 번 당겼다",
    # 피로·무력감
    "지쳐있었다":                   "눈꺼풀이 납 같았다",
    "무기력했다":                   "팔 하나 들기가 힘들었다",
    # 그리움·향수
    "그리웠다":                     "그 냄새가 코끝에 맴도는 것 같았다",
    "보고 싶었다":                  "핸드폰을 집어들다가 내려놓았다",
    # 행복
    "행복했다":                     "발끝까지 따뜻한 것 같았다",
    "포근했다":                     "숨을 한 번 깊이 들이쉬었다",
}

# ── 장르별 추가 사전 ───────────────────────────────────────────────────
_GENRE_ADDITIONS: Dict[str, Dict[str, str]] = {
    "noir": {
        "불안했다":     "담배 연기가 눈에 들어오는 것처럼 따가웠다",
        "두려웠다":     "코트 주머니 속 손이 아무것도 잡지 않았다",
        "믿기지 않았다": "창밖의 가로등을 다섯 번 세었다",
    },
    "fantasy": {
        "두려웠다":     "마법의 기운이 손끝에서 흩어지는 것 같았다",
        "기쁨이 넘쳤다": "빛이 가슴 안쪽에서 터지는 것 같았다",
    },
    "romance": {
        "심장이 두근거렸다": "그 손이 닿았던 자리가 한참 뒤까지 따뜻했다",
        "부끄러웠다":   "귀 끝까지 열기가 번졌다",
    },
    "historical": {
        "분노가 치밀었다": "옷깃을 여몄다",
        "각오를 다졌다":  "손을 모아 예를 올렸다",
    },
}

# ── 공통 허용 패턴 (교체 면제) ──────────────────────────────────────────
_EXEMPT_PATTERNS: List[str] = [
    r"그리움이라는 이름의",  # 의도적 표현
]


@dataclass
class AntiLLMFilterResult:
    filtered:     str
    score:        float
    replacements: List[Tuple[str, str]] = field(default_factory=list)
    n_cliches:    int = 0

    @property
    def is_clean(self) -> bool:
        return self.n_cliches == 0


class KoreanAntiLLMFilter:
    """
    한국 드라마 AI 클리셰를 구체적 감각어로 교체하는 필터.
    NarrativeScopeResolver 장르 플러그인과 연동하여 장르별 허용 표현을 차별화한다.
    """

    def __init__(self, genre_id: str = "literary") -> None:
        self.genre_id = genre_id
        self._dict: Dict[str, str] = self._load_dict(genre_id)

    def _load_dict(self, genre_id: str) -> Dict[str, str]:
        d = dict(_BASE_DICT)
        d.update(_GENRE_ADDITIONS.get(genre_id, {}))
        return d

    def _is_exempt(self, text: str) -> bool:
        return any(re.search(p, text) for p in _EXEMPT_PATTERNS)

    def filter(self, text: str) -> FilterResult:
        """텍스트에서 클리셰를 탐지·교체하고 FilterResult를 반환한다."""
        result = text
        replacements: List[Tuple[str, str]] = []

        for cliche, replacement in sorted(self._dict.items(), key=lambda x: -len(x[0])):
            if cliche in result and not self._is_exempt(cliche):
                result = result.replace(cliche, replacement)
                replacements.append((cliche, replacement))

        n = len(replacements)
        # 점수: 원본 대비 클리셰 밀도 역수 (최대 10.0)
        if len(text) == 0:
            score = 10.0
        else:
            # 클리셰 누적 길이 / 전체 텍스트 길이 비율의 역수
            cliche_chars = sum(len(c) for c, _ in replacements)
            ratio = min(cliche_chars / max(len(text), 1), 1.0)
            score = round(10.0 * (1.0 - ratio), 3)

        return FilterResult(filtered=result, score=score,
                            replacements=replacements, n_cliches=n)

    def score_only(self, text: str) -> float:
        """텍스트의 클리셰 점수만 반환 (교체 없음)."""
        return self.filter(text).score

    @property
    def dict_size(self) -> int:
        return len(self._dict)

FilterResult = AntiLLMFilterResult  # V579 backward-compat alias
