"""
V315: KnowledgeStateTracker
인물 지식 비대칭 추적 — 세계 시뮬레이션의 첫 구현.

핵심 질문:
  - 누가 무엇을 알고 있는가
  - 누가 무엇을 오해하는가
  - 누가 무엇을 의심하는가
  - 이 비대칭이 어떤 장면 압력을 만드는가

지식 비대칭이 장면 압력의 원천.
A가 B의 배신을 모를 때, 둘이 함께 있는 장면의 압력은 극대화된다.
독자는 알고 인물은 모른다 → 공포
인물이 알고 독자는 모른다 → 서스펜스
둘 다 모른다 → 미스터리

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class KnowledgeStatus(str, Enum):
    KNOWS       = "knows"       # 확실히 앎
    SUSPECTS    = "suspects"    # 의심함
    UNAWARE     = "unaware"     # 전혀 모름
    MISBELIEVES = "misbelieves" # 잘못 알고 있음
    READER_ONLY = "reader_only" # 독자만 앎 (인물은 모름)


class InformationType(str, Enum):
    IDENTITY    = "identity"    # 인물의 정체
    BETRAYAL    = "betrayal"    # 배신 여부
    LOCATION    = "location"    # 위치 정보
    MOTIVE      = "motive"      # 동기
    RELATIONSHIP= "relationship"# 관계
    EVENT       = "event"       # 사건 발생
    OBJECT      = "object"      # 오브제 존재/위치
    PLAN        = "plan"        # 계획


@dataclass
class KnowledgeFact:
    """세계 안의 하나의 사실."""
    fact_id: str
    fact_type: InformationType
    description: str
    true_value: str                # 실제 사실
    episode_revealed_at: int = 0   # 이 사실이 세계에 존재하기 시작한 화


@dataclass
class CharacterKnowledge:
    """특정 인물이 특정 사실에 대해 알고 있는 상태."""
    char_id: str
    fact_id: str
    status: KnowledgeStatus
    believed_value: str = ""       # misbelieves일 때 잘못 알고 있는 값
    episode_learned: int = 0       # 알게 된 화
    how_learned: str = ""          # 어떻게 알게 됐는가


@dataclass
class AsymmetryReport:
    """두 인물 간의 지식 비대칭 분석."""
    char_a: str
    char_b: str
    fact_id: str
    asymmetry_type: str   # "a_knows_b_doesnt", "b_knows_a_doesnt", "both_know", "neither_knows"
    pressure_score: float # 이 비대칭이 만드는 장면 압력 [0, 1]
    dramatic_potential: str  # 드라마틱 포텐셜 설명


class KnowledgeStateTracker:
    """
    프로젝트 전체의 인물 지식 상태를 추적.
    화 진행에 따라 지식 상태가 변화하고,
    이 비대칭이 장면 압력을 결정한다.
    """

    def __init__(self, project_id: str):
        self.project_id = project_id

        # 세계의 사실들 {fact_id: KnowledgeFact}
        self.facts: dict[str, KnowledgeFact] = {}

        # 인물별 지식 상태 {char_id: {fact_id: CharacterKnowledge}}
        self.char_knowledge: dict[str, dict[str, CharacterKnowledge]] = {}

        # 독자 지식 (독자는 항상 더 많이 안다고 가정)
        self.reader_knowledge: set[str] = set()  # 독자가 아는 fact_id들

        # 지식 변화 로그 {episode_no: [변화 기록]}
        self.change_log: dict[int, list[dict]] = {}

    # ── 사실 등록 ─────────────────────────────────────────
    def register_fact(
        self,
        fact_id: str,
        fact_type: InformationType | str,
        description: str,
        true_value: str,
        episode_revealed_at: int = 1,
        reader_knows: bool = True,
    ) -> KnowledgeFact:
        """세계의 사실 하나를 등록."""
        if isinstance(fact_type, str):
            fact_type = InformationType(fact_type)

        fact = KnowledgeFact(
            fact_id=fact_id,
            fact_type=fact_type,
            description=description,
            true_value=true_value,
            episode_revealed_at=episode_revealed_at,
        )
        self.facts[fact_id] = fact
        if reader_knows:
            self.reader_knowledge.add(fact_id)
        return fact

    # ── 인물 지식 상태 설정 ───────────────────────────────
    def set_knowledge(
        self,
        char_id: str,
        fact_id: str,
        status: KnowledgeStatus | str,
        episode_no: int,
        believed_value: str = "",
        how_learned: str = "",
    ) -> None:
        """인물의 특정 사실에 대한 지식 상태를 설정."""
        if isinstance(status, str):
            status = KnowledgeStatus(status)

        if char_id not in self.char_knowledge:
            self.char_knowledge[char_id] = {}

        ck = CharacterKnowledge(
            char_id=char_id,
            fact_id=fact_id,
            status=status,
            believed_value=believed_value,
            episode_learned=episode_no,
            how_learned=how_learned,
        )
        self.char_knowledge[char_id][fact_id] = ck

        # 변화 로그
        if episode_no not in self.change_log:
            self.change_log[episode_no] = []
        self.change_log[episode_no].append({
            "char_id": char_id,
            "fact_id": fact_id,
            "status": status.value,
            "how": how_learned,
        })

    def get_knowledge(self, char_id: str, fact_id: str) -> KnowledgeStatus:
        """인물의 특정 사실에 대한 현재 지식 상태."""
        ck = self.char_knowledge.get(char_id, {}).get(fact_id)
        if ck is None:
            return KnowledgeStatus.UNAWARE
        return ck.status

    # ── 지식 비대칭 분석 ──────────────────────────────────
    def analyze_asymmetry(
        self, char_a: str, char_b: str, fact_id: str
    ) -> AsymmetryReport:
        """두 인물 간의 특정 사실에 대한 지식 비대칭."""
        status_a = self.get_knowledge(char_a, fact_id)
        status_b = self.get_knowledge(char_b, fact_id)
        reader_knows = fact_id in self.reader_knowledge

        # 비대칭 유형 분류
        a_knows = status_a in (KnowledgeStatus.KNOWS, KnowledgeStatus.SUSPECTS)
        b_knows = status_b in (KnowledgeStatus.KNOWS, KnowledgeStatus.SUSPECTS)

        if a_knows and not b_knows:
            asym_type = "a_knows_b_doesnt"
            pressure = 0.75 if status_a == KnowledgeStatus.KNOWS else 0.55
            dramatic = f"{char_a}는 알고 {char_b}는 모름 → {char_a}가 주도권 보유, 장면 긴장↑"
        elif b_knows and not a_knows:
            asym_type = "b_knows_a_doesnt"
            pressure = 0.75 if status_b == KnowledgeStatus.KNOWS else 0.55
            dramatic = f"{char_b}는 알고 {char_a}는 모름 → {char_b}가 주도권 보유, 장면 긴장↑"
        elif a_knows and b_knows:
            asym_type = "both_know"
            pressure = 0.30
            dramatic = "둘 다 앎 → 공개 대결 가능, 표면 긴장 낮음"
        else:
            asym_type = "neither_knows"
            pressure = 0.20 if not reader_knows else 0.45
            dramatic = "둘 다 모름 → 미스터리 유지" if not reader_knows else "독자만 앎 → 공포/아이러니"

        # misbelieves 보정
        if status_a == KnowledgeStatus.MISBELIEVES or status_b == KnowledgeStatus.MISBELIEVES:
            pressure = min(1.0, pressure + 0.20)
            dramatic += " (오해 포함 → 충돌 위험 ↑↑)"

        # 독자-인물 비대칭 보정 (독자가 알고 인물이 모를 때 → 극적 아이러니)
        if reader_knows and not a_knows and not b_knows:
            pressure = min(1.0, pressure + 0.15)

        return AsymmetryReport(
            char_a=char_a,
            char_b=char_b,
            fact_id=fact_id,
            asymmetry_type=asym_type,
            pressure_score=round(pressure, 3),
            dramatic_potential=dramatic,
        )

    def scene_pressure_from_knowledge(
        self,
        characters_in_scene: list[str],
        facts_in_play: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        씬에 등장하는 인물들 사이의 지식 비대칭이
        만들어내는 총 장면 압력 계산.
        """
        if len(characters_in_scene) < 2:
            return {"total_pressure": 0.0, "asymmetries": [], "dominant_tension": None}

        facts_to_check = facts_in_play or list(self.facts.keys())
        asymmetries = []

        for i, char_a in enumerate(characters_in_scene):
            for char_b in characters_in_scene[i+1:]:
                for fact_id in facts_to_check:
                    report = self.analyze_asymmetry(char_a, char_b, fact_id)
                    if report.pressure_score > 0.30:  # 유의미한 비대칭만
                        asymmetries.append(report)

        if not asymmetries:
            return {"total_pressure": 0.0, "asymmetries": [], "dominant_tension": None}

        # 총 압력: 개별 비대칭의 가중 합
        pressures = [a.pressure_score for a in asymmetries]
        total = round(min(1.0, sum(pressures) / max(len(pressures), 1) * 1.3), 3)

        # 가장 강한 비대칭
        dominant = max(asymmetries, key=lambda x: x.pressure_score)

        return {
            "total_pressure": total,
            "asymmetry_count": len(asymmetries),
            "asymmetries": [
                {
                    "chars": f"{a.char_a}↔{a.char_b}",
                    "fact": a.fact_id,
                    "type": a.asymmetry_type,
                    "pressure": a.pressure_score,
                    "dramatic": a.dramatic_potential,
                }
                for a in sorted(asymmetries, key=lambda x: -x.pressure_score)
            ],
            "dominant_tension": {
                "chars": f"{dominant.char_a}↔{dominant.char_b}",
                "fact": dominant.fact_id,
                "pressure": dominant.pressure_score,
                "dramatic": dominant.dramatic_potential,
            },
        }

    # ── 지식 전파 ─────────────────────────────────────────
    def propagate_knowledge(
        self,
        from_char: str,
        to_char: str,
        fact_id: str,
        episode_no: int,
        how: str = "직접 말함",
        partial: bool = False,
    ) -> None:
        """
        한 인물이 다른 인물에게 사실을 알려줌.
        partial=True: 일부만 알려줌 → suspects 상태
        """
        from_status = self.get_knowledge(from_char, fact_id)
        if from_status not in (KnowledgeStatus.KNOWS, KnowledgeStatus.SUSPECTS):
            return  # 모르는 것을 전달할 수 없음

        fact = self.facts.get(fact_id)
        if not fact:
            return

        new_status = KnowledgeStatus.SUSPECTS if partial else KnowledgeStatus.KNOWS
        self.set_knowledge(
            char_id=to_char,
            fact_id=fact_id,
            status=new_status,
            episode_no=episode_no,
            believed_value=fact.true_value if not partial else f"부분적: {fact.true_value}",
            how_learned=how,
        )

    def introduce_misbelief(
        self,
        char_id: str,
        fact_id: str,
        false_value: str,
        episode_no: int,
        how: str = "잘못된 정보",
    ) -> None:
        """인물에게 잘못된 믿음 심기 — 반전의 씨앗."""
        self.set_knowledge(
            char_id=char_id,
            fact_id=fact_id,
            status=KnowledgeStatus.MISBELIEVES,
            episode_no=episode_no,
            believed_value=false_value,
            how_learned=how,
        )

    # ── 화 단위 요약 ──────────────────────────────────────
    def episode_knowledge_summary(self, episode_no: int) -> dict[str, Any]:
        """특정 화 기준 전체 지식 상태 요약."""
        changes = self.change_log.get(episode_no, [])
        # 전체 비대칭 압력 평균
        total_chars = list(self.char_knowledge.keys())
        all_facts = list(self.facts.keys())
        pressures = []
        for i, ca in enumerate(total_chars):
            for cb in total_chars[i+1:]:
                for fid in all_facts:
                    r = self.analyze_asymmetry(ca, cb, fid)
                    if r.pressure_score > 0:
                        pressures.append(r.pressure_score)

        avg_pressure = round(sum(pressures) / max(len(pressures), 1), 3) if pressures else 0.0

        return {
            "episode_no": episode_no,
            "changes_this_episode": changes,
            "total_facts": len(self.facts),
            "total_characters_tracked": len(self.char_knowledge),
            "avg_knowledge_pressure": avg_pressure,
            "misbeliefs_active": sum(
                1 for ck_dict in self.char_knowledge.values()
                for ck in ck_dict.values()
                if ck.status == KnowledgeStatus.MISBELIEVES
            ),
        }


class CausalChainPlanner:
    """
    인과 연쇄 계획.
    "A가 B를 알게 되면 → 몇 화 뒤 C에게 어떤 압력이 생기는가"를 예측.

    V315의 세계 시뮬레이션 핵심 이론:
    바둑의 "몇 수 뒤 형세 계산"에 해당.
    """

    def __init__(self, tracker: KnowledgeStateTracker):
        self.tracker = tracker

    def predict_pressure_shift(
        self,
        if_char_learns: str,
        fact_id: str,
        current_episode: int,
        look_ahead: int = 3,
    ) -> dict[str, Any]:
        """
        만약 특정 인물이 특정 사실을 알게 된다면,
        이후 look_ahead화 동안 어떤 압력 변화가 생기는가?
        """
        # 현재 압력 계산
        all_chars = list(self.tracker.char_knowledge.keys())
        if if_char_learns not in all_chars:
            all_chars.append(if_char_learns)

        current_pressures = {}
        for other in all_chars:
            if other == if_char_learns:
                continue
            r = self.tracker.analyze_asymmetry(if_char_learns, other, fact_id)
            current_pressures[other] = r.pressure_score

        # 가상: 해당 인물이 알게 된 후 압력 변화
        fact = self.tracker.facts.get(fact_id)
        if not fact:
            return {"error": f"fact {fact_id} not found"}

        # 임시 알게 됨 → 비대칭 반전
        predicted_shifts = {}
        for other in all_chars:
            if other == if_char_learns:
                continue
            other_status = self.tracker.get_knowledge(other, fact_id)
            other_knows = other_status in (KnowledgeStatus.KNOWS, KnowledgeStatus.SUSPECTS)

            if other_knows:
                # 둘 다 알게 됨 → 압력 감소, 대결 가능
                new_pressure = 0.35
                shift_type = "knowledge_equalized_confrontation_possible"
            else:
                # 정보 습득자가 우위 → 새 긴장 구조
                new_pressure = 0.72
                shift_type = "new_information_advantage"

            predicted_shifts[other] = {
                "before": current_pressures.get(other, 0.0),
                "after": new_pressure,
                "delta": round(new_pressure - current_pressures.get(other, 0.0), 3),
                "shift_type": shift_type,
            }

        max_delta_char = max(predicted_shifts.items(),
                              key=lambda x: abs(x[1]["delta"])) if predicted_shifts else None

        return {
            "if_char": if_char_learns,
            "fact_id": fact_id,
            "current_episode": current_episode,
            "predicted_payoff_episode": current_episode + look_ahead,
            "pressure_shifts": predicted_shifts,
            "biggest_shift": {
                "toward_char": max_delta_char[0] if max_delta_char else None,
                "delta": max_delta_char[1]["delta"] if max_delta_char else 0.0,
            } if max_delta_char else None,
            "recommendation": self._recommend(predicted_shifts),
        }

    def _recommend(self, shifts: dict) -> str:
        if not shifts:
            return "변화 없음"
        max_delta = max(abs(v["delta"]) for v in shifts.values())
        if max_delta > 0.35:
            return "강력한 반전 포텐셜 — 이 사실 공개를 핵심 reveal로 설계 권장"
        elif max_delta > 0.15:
            return "중간 반전 포텐셜 — 점진적 누출로 압력 유지 권장"
        else:
            return "압력 변화 미미 — reveal 타이밍 재검토 권장"

    def cascade_chain(
        self,
        initial_reveal: str,    # fact_id
        initial_learner: str,   # char_id
        episode_no: int,
        depth: int = 3,
    ) -> list[dict[str, Any]]:
        """
        연쇄 반응 예측.
        A가 X를 알면 → B에게 어떤 영향 → C에게 어떤 영향 ...
        """
        chain = []
        current_fact = initial_reveal
        current_learner = initial_learner
        current_ep = episode_no

        for step in range(depth):
            prediction = self.predict_pressure_shift(
                current_learner, current_fact, current_ep, look_ahead=1
            )
            chain.append({
                "step": step + 1,
                "episode": current_ep,
                "learner": current_learner,
                "fact": current_fact,
                "prediction": prediction,
            })

            # 다음 연쇄: 가장 큰 영향을 받는 인물이 다음 단계의 중심
            biggest = prediction.get("biggest_shift")
            if biggest and biggest["toward_char"]:
                current_learner = biggest["toward_char"]
                current_ep += 1
            else:
                break

        return chain
