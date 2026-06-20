"""learning/pairing — P0 선호쌍 빌더 (DESIGN-P0-PAIRING-BUILDER-v1).

DPO 학습용 선호쌍을 결정론(GPU 불요)으로 생성한다. 오염 3대 경로
(길이 confound·암기/표절·AI-judge-AI 순환편향)를 입구에서 차단한다.

불변식
- I1 per-token only      : 채점은 per-token만, sum 경로 3중 차단(assert_no_sum)
- I2 length neutrality    : token |Δ|/max ≤ 5% hard, char ≤ 8% soft
- I3 no verbatim          : 산출물(ledger)에 명작 원문 텍스트 0 (통계만)
- I4 work-level split     : 같은 작품이 train/held 동시출현 금지, held ≥ 250
- I5 tokenizer lock       : 단일 토크나이저 + tokenizer_sha 기록·동결
"""
from .splits import work_level_split, SplitResult, LeakError
from .length_match import length_match_decision, LengthMatch, TOKEN_HARD, CHAR_SOFT
from .tokenizer import Tokenizer, WhitespaceTokenizer, tokenizer_sha

__all__ = [
    "work_level_split", "SplitResult", "LeakError",
    "length_match_decision", "LengthMatch", "TOKEN_HARD", "CHAR_SOFT",
    "Tokenizer", "WhitespaceTokenizer", "tokenizer_sha",
]
