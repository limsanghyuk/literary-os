"""
V321-B: KnowledgeBoundaryGate
V321-C: DRSE Engine (SemanticScorer + DRSEScorer + DRSEContextRouter)

설계 원칙 (3인 합의 + AETHER 합의):
  - KnowledgeBoundaryGate: V320 KST API 완전 호환
  - SemanticScorer: 교체 가능 인터페이스 (TF-IDF → Embedding)
  - FORBIDDEN_KNOWLEDGE_BOUNDARY: AETHER 아이디어 채택
  - absolute_gates: 하나라도 0 → 즉시 0.0
  - ContextPacket: allowed + forbidden + rendering_strategy

LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from literary_system.relation_graph.relation_graph_store import NodeType, RelationGraphStore, RelationType, StoryNode

# ══════════════════════════════════════════════════════════════════
# V321-B: KnowledgeBoundaryGate
# ══════════════════════════════════════════════════════════════════

class KnowledgeBoundaryGate:
    """
    V320 KnowledgeStateTracker API와 완전 호환.
    인물 지식 상태 → DRSE 주입 가중치 변환.

    상태별 가중치:
      KNOWS        = 1.0  완전 주입
      SUSPECTS     = 0.5  암시 형태만
      MISBELIEVES  = 0.4  왜곡 버전으로
      UNAWARE      = 0.0  완전 차단 (전지적 환각 방지)
      READER_ONLY  = 1.0 (전지 시점) / 0.0 (인물 시점)
      hides_from   = 0.0  숨겨진 정보 차단

    [RGS 기반 가중치도 병렬 사용]
    RelationGraphStore의 엣지 타입으로 보완 판정.
    """

    WEIGHT_MAP = {
        "knows":         1.0,
        "suspects":      0.5,
        "misbelieves":   0.4,
        "UNAWARE":       0.0,
        "does_not_know": 0.0,
        "hides_from":    0.0,
        "revealed_to":   1.0,
    }

    def __init__(
        self,
        knowledge_tracker=None,   # V320 KnowledgeStateTracker (선택)
        relation_graph: RelationGraphStore | None = None,
    ):
        self.tracker = knowledge_tracker
        self.rgs = relation_graph

    def calculate_gate_weight(
        self,
        node: StoryNode,
        pov_character: str,
        is_omniscient_pov: bool = False,
    ) -> float:
        """
        0.0~1.0 가중치 반환.
        0.0 = 이 노드는 ContextPacket에서 차단.
        """
        # ① RGS 엣지 기반 판정 (우선)
        if self.rgs:
            rgs_status = self.rgs.get_knowledge_status(pov_character, node.node_id)
            if rgs_status != "UNAWARE":
                w = self.WEIGHT_MAP.get(rgs_status, 0.0)
                # READER_ONLY 처리
                if rgs_status == "reader_only":
                    return 1.0 if is_omniscient_pov else 0.0
                return w

        # ② V320 KnowledgeStateTracker 기반 판정
        if self.tracker:
            try:
                status = self.tracker.get_knowledge(pov_character, node.node_id)
                status_val = status.value if hasattr(status, "value") else str(status)
                if status_val == "reader_only":
                    return 1.0 if is_omniscient_pov else 0.0
                return self.WEIGHT_MAP.get(status_val, 0.0)
            except Exception:
                pass

        # ③ 기본값: 차단 (안전 우선)
        return 0.0 if node.node_type == NodeType.FACT_SECRET else 1.0


# ══════════════════════════════════════════════════════════════════
# V321-C: SemanticScorer (교체 가능 인터페이스)
# ══════════════════════════════════════════════════════════════════

class SemanticScorer(ABC):
    """교체 가능 의미 유사도 스코어러 인터페이스."""
    @abstractmethod
    def score(self, node_text: str, scene_goal: str) -> float:
        """[0, 1] 범위 유사도 반환."""
        ...


class TFIDFSemanticScorer(SemanticScorer):
    """TF-IDF 기반 즉시 구현. EmbeddingSemanticScorer로 나중에 교체 가능."""

    def score(self, node_text: str, scene_goal: str) -> float:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            if not node_text.strip() or not scene_goal.strip():
                return 0.0
            vec = TfidfVectorizer().fit_transform([node_text, scene_goal])
            return float(cosine_similarity(vec[0], vec[1])[0][0])
        except Exception:
            return self._keyword_fallback(node_text, scene_goal)

    def _keyword_fallback(self, a: str, b: str) -> float:
        """sklearn 없을 때 키워드 겹침 비율."""
        a_words = set(a.split())
        b_words = set(b.split())
        if not a_words or not b_words:
            return 0.0
        return len(a_words & b_words) / max(len(a_words | b_words), 1)


class KeywordSemanticScorer(SemanticScorer):
    """가장 단순한 키워드 겹침 스코어러 (테스트용)."""
    def score(self, node_text: str, scene_goal: str) -> float:
        a = set(node_text.split())
        b = set(scene_goal.split())
        if not a or not b:
            return 0.0
        return len(a & b) / max(len(a | b), 1)

class DualSemanticScorer(SemanticScorer):
    """V402 — TF-IDF + NKG BM25+RRF 병렬 실행 스코어러 (3인 합의안).

    NKG 없거나 비었으면 TF-IDF 단독.
    NKG 활성화 시 max(tfidf, nkg) 반환 — 점진적 품질 향상.
    기존 TFIDFSemanticScorer와 100% backward compatible.
    """

    def __init__(
        self,
        tfidf: "SemanticScorer | None" = None,
        nkg_adapter: "object | None" = None,   # NKGSemanticAdapter (선택)
    ) -> None:
        self._tfidf = tfidf or TFIDFSemanticScorer()
        self._nkg = nkg_adapter   # NKGSemanticAdapter | None

    def score(self, node_text: str, scene_goal: str) -> float:
        s_tfidf = self._tfidf.score(node_text, scene_goal)
        if self._nkg is None:
            return s_tfidf
        try:
            if not self._nkg.is_ready():
                return s_tfidf
            s_nkg = self._nkg.score(node_text, scene_goal)
            return max(s_tfidf, s_nkg)
        except Exception:
            return s_tfidf




# ══════════════════════════════════════════════════════════════════
# V321-C: DRSEScorer — 9항 공식
# ══════════════════════════════════════════════════════════════════

@dataclass
class NodeScore:
    node: StoryNode
    score: float
    gate_blocked: bool = False
    is_forbidden_secret: bool = False
    breakdown: dict[str, float] = field(default_factory=dict)


class DRSEScorer:
    """
    DRSE 9항 공식 연산기.

    RelationalScore = (S × R × T) × (A × C × P) × (G₁ × G₂ × G₃)

    S = SemanticRelevance      (TF-IDF 또는 Embedding)
    R = RelationStrength       (엣지 strength)
    T = TemporalDecay          (시간 감쇠)
    A = CharacterArcPressure   (인물 아크 압력)
    C = UnresolvedResidueBoost (미회수 복선 부스트)
    P = AuthorityRiskPenalty   (권한 침범 패널티, V322)
    G₁= RevealBudgetGate       (공개 예산 게이트)
    G₂= KnowledgeBoundaryGate  (인식 경계 차단)
    G₃= CanonConsistencyGate   (캐논 일관성)

    AbsoluteGates (G₁×G₂×G₃): 하나라도 0 → 즉시 0.0
    """

    DECAY_LAMBDA: float = 0.05
    ARC_PRESSURE_TYPES: tuple = ("CHARACTER_TRAUMA", "CHARACTER")
    ARC_PRESSURE_BOOST: float = 1.2
    RESIDUE_BOOST: float = 1.5
    RESIDUE_MIN_S: float = 0.15    # [버그 1 수정] TF-IDF S=0 시 복선 최솟값 보장

    def __init__(
        self,
        rgs: RelationGraphStore,
        boundary_gate: KnowledgeBoundaryGate,
        semantic_scorer: SemanticScorer | None = None,
        causal_planner=None,    # V320 CausalChainPlanner (선택)
        payoff_scheduler=None,  # V320 PayoffScheduler (선택)
        nkg=None,               # V402: NKGGraphStore (선택) — DualSemanticScorer 활성화
    ):
        self.rgs = rgs
        self.boundary_gate = boundary_gate
        # V402: nkg 주입 시 DualSemanticScorer, 없으면 기존 TFIDFSemanticScorer
        if semantic_scorer is not None:
            self.semantic = semantic_scorer
        elif nkg is not None:
            try:
                from literary_system.nkg.adapters.nkg_semantic_adapter import NKGSemanticAdapter
                nkg_adapter = NKGSemanticAdapter(nkg)
                self.semantic = DualSemanticScorer(TFIDFSemanticScorer(), nkg_adapter)
            except ImportError:
                self.semantic = TFIDFSemanticScorer()
        else:
            self.semantic = TFIDFSemanticScorer()
        self.causal = causal_planner
        self.payoff = payoff_scheduler

    def score_node(
        self,
        node: StoryNode,
        scene_goal: str,
        pov_character: str,
        current_episode: int,
        is_omniscient_pov: bool = False,
    ) -> NodeScore:
        """단일 노드 9항 스코어 계산."""

        breakdown: dict[str, float] = {}

        # ── G₁ RevealBudgetGate ──────────────────────────────────
        if node.reveal_episode and current_episode < node.reveal_episode:
            g1 = 0.0
        else:
            g1 = 1.0
        breakdown["G1_reveal_budget"] = g1

        # ── G₂ KnowledgeBoundaryGate ────────────────────────────
        g2 = self.boundary_gate.calculate_gate_weight(
            node, pov_character, is_omniscient_pov
        )
        breakdown["G2_knowledge_boundary"] = g2

        # ── G₃ CanonConsistencyGate ─────────────────────────────
        g3 = 1.0  # V322에서 ForbiddenRevealScanner 연동
        breakdown["G3_canon_consistency"] = g3

        # ── AbsoluteGates ───────────────────────────────────────
        absolute_gates = g1 * g2 * g3
        is_blocked = (absolute_gates == 0.0)
        is_forbidden_secret = (
            is_blocked and node.node_type in (NodeType.FACT_SECRET, "SECRET")
        )

        if is_blocked:
            return NodeScore(
                node=node, score=0.0,
                gate_blocked=True,
                is_forbidden_secret=is_forbidden_secret,
                breakdown=breakdown,
            )

        # ── S SemanticRelevance ──────────────────────────────────
        s = max(0.0, self.semantic.score(node.content, scene_goal))
        breakdown["S_semantic"] = s

        # ── R RelationStrength ───────────────────────────────────
        r = self.rgs.get_edge_strength(pov_character, node.node_id)
        breakdown["R_relation_strength"] = r

        # ── T TemporalDecay ──────────────────────────────────────
        delta_t = max(0, current_episode - node.origin_episode)
        t = math.exp(-self.DECAY_LAMBDA * delta_t)
        breakdown["T_temporal_decay"] = round(t, 4)

        # ── A CharacterArcPressure ───────────────────────────────
        a = self.ARC_PRESSURE_BOOST if node.node_type in self.ARC_PRESSURE_TYPES else 1.0
        if self.causal:
            try:
                pred = self.causal.predict_pressure_shift(
                    pov_character, node.node_id, current_episode
                )
                biggest = pred.get("biggest_shift", {})
                if biggest.get("delta", 0) > 0.3:
                    a = min(a * 1.3, 2.0)
            except Exception:
                pass
        breakdown["A_arc_pressure"] = a

        # ── C UnresolvedResidueBoost ─────────────────────────────
        # [버그 1 수정] S=0 충돌 방지
        # TF-IDF 형태소 불일치로 S=0이 되면 base=0 → 부스트 무력화.
        # 미회수 복선은 씬과 직접 관련 없어도 최소 점수를 보장해야 함.
        # 해결: is_unresolved_residue=True일 때 s에 최솟값 RESIDUE_MIN_S 적용.
        is_unresolved_residue = (
            node.node_type in (NodeType.FORESHADOWING, NodeType.OBJECT_RESIDUE)
            and not node.is_resolved
        )
        if is_unresolved_residue and s < self.RESIDUE_MIN_S:
            s = self.RESIDUE_MIN_S   # 최솟값 보장 (EmbeddingScorer 전환 전 보정)
            breakdown["S_semantic"] = s
        c = self.RESIDUE_BOOST if is_unresolved_residue else 1.0
        breakdown["C_residue_boost"] = c

        # ── P AuthorityRiskPenalty (V322 완성) ───────────────────
        p = 0.5 if node.node_type == NodeType.WORLD_RULE else 1.0
        breakdown["P_authority_penalty"] = p

        # ── 최종 스코어 ──────────────────────────────────────────
        base   = s * r * t
        boosts = a * c * p
        final  = base * boosts * absolute_gates
        breakdown["final"] = round(final, 6)

        return NodeScore(
            node=node, score=final,
            gate_blocked=False,
            is_forbidden_secret=False,
            breakdown=breakdown,
        )

    def score_all(
        self,
        scene_goal: str,
        pov_character: str,
        current_episode: int,
        is_omniscient_pov: bool = False,
    ) -> list[NodeScore]:
        """전체 노드 스코어링."""
        return [
            self.score_node(n, scene_goal, pov_character,
                            current_episode, is_omniscient_pov)
            for n in self.rgs.all_nodes()
        ]


# ══════════════════════════════════════════════════════════════════
# V321-C: DRSEContextRouter — ContextPacket 생성
# ══════════════════════════════════════════════════════════════════

@dataclass
class ContextPacket:
    """Node2에 전달하는 행동 강령 패킷."""
    scene_goal: str
    pov_character: str
    episode_no: int
    allowed_context: list[str]
    forbidden_context: list[str]         # AETHER 아이디어: score=0 SECRET 명시
    rendering_strategy: list[str]
    drse_scores: dict[str, float]        # {node_id: score}
    top_node_ids: list[str]              # 상위 K개 node_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_goal": self.scene_goal,
            "pov_character": self.pov_character,
            "episode_no": self.episode_no,
            "allowed_context": self.allowed_context,
            "forbidden_context": self.forbidden_context,
            "rendering_strategy": self.rendering_strategy,
            "drse_scores": self.drse_scores,
            "top_node_ids": self.top_node_ids,
        }


class DRSEContextRouter:
    """
    9항 스코어 기반 ContextPacket 조립.

    AETHER 합의 반영:
      - score=0이지만 SECRET 타입인 노드 →
        forbidden_context에 명시적 금지 문구 추가 (이중 잠금장치)
    """

    DEFAULT_RENDERING_STRATEGY = [
        "allowed_context의 정보만 활용하여 렌더링",
        "forbidden_context의 정보는 대사/내면에 절대 포함 금지",
        "직접 감정 표현 금지 — 행동과 오브제로 간접 표현 (PDI 준수)",
        "SUSPECTS 상태 정보는 암시와 서브텍스트로만 표현",
    ]

    def __init__(self, scorer: DRSEScorer):
        self.scorer = scorer

    def build_packet(
        self,
        scene_goal: str,
        pov_character: str,
        current_episode: int,
        top_k: int = 5,
        is_omniscient_pov: bool = False,
        extra_strategy: list[str] | None = None,
    ) -> ContextPacket:
        """ContextPacket 생성."""

        all_scores = self.scorer.score_all(
            scene_goal, pov_character, current_episode, is_omniscient_pov
        )

        allowed_context: list[str] = []
        forbidden_context: list[str] = []
        drse_scores: dict[str, float] = {}

        for ns in all_scores:
            drse_scores[ns.node.node_id] = round(ns.score, 4)

            if ns.gate_blocked:
                # AETHER 아이디어: SECRET은 forbidden_context에 명시
                if ns.is_forbidden_secret:
                    forbidden_context.append(
                        f"[절대 금지] 인물 '{pov_character}'는 "
                        f"'{ns.node.content}' 사실을 모름. "
                        f"이 정보가 대사/내면에 나타나면 즉시 REJECT."
                    )
            else:
                allowed_context.append(ns.node.content)

        # 상위 K개 선별
        passed = [(ns.node.node_id, ns.score)
                  for ns in all_scores if not ns.gate_blocked and ns.score > 0]
        passed.sort(key=lambda x: x[1], reverse=True)
        top_k_ids = [nid for nid, _ in passed[:top_k]]
        top_k_context = [
            self.scorer.rgs.get_node(nid).content
            for nid in top_k_ids
            if self.scorer.rgs.get_node(nid)
        ]

        strategy = list(self.DEFAULT_RENDERING_STRATEGY)
        if extra_strategy:
            strategy.extend(extra_strategy)

        return ContextPacket(
            scene_goal=scene_goal,
            pov_character=pov_character,
            episode_no=current_episode,
            allowed_context=top_k_context,
            forbidden_context=forbidden_context,
            rendering_strategy=strategy,
            drse_scores=drse_scores,
            top_node_ids=top_k_ids,
        )
