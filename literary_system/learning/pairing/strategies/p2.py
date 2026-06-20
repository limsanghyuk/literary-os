from .base import BaseStrategy
class P2OnPolicy(BaseStrategy):
    name = "p2"
    description = "on-policy 20%. 현 정책 생성물 vs 개선 후보."
