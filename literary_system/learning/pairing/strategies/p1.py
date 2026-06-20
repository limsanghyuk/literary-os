from .base import BaseStrategy
class P1GradedDegradation(BaseStrategy):
    name = "p1"
    description = ("등급화 열화쌍 15%. 열화 4축 중 텍스트 단축 축은 길이매칭+"
                   "break_causality(길이중립) 가중으로 V788 길이교란 재유입 차단.")
