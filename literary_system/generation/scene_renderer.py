"""scene_renderer — G1 검증 통과(2026-08-03, Δ=+0.79) 시퀀스 캐스케이드 렌더러.

docs/design/2026-07-03_sceneblueprint_vertical_slice/의 소비자 프로토타입 3본을
엔진 정식 모듈로 승격한 것 (감사 처방: docs/design → literary_system).
- 조건 A(카드만) 대비 조건 B(+시퀀스 컨텍스트) 실측: Δ기능 +0.90, Δ사실 +0.47, Δ밀도 +1.00.
- 렌더러 LLM은 주입식(GenerateFn) — pass_pipeline의 소켓 규약과 동일.
"""
from dataclasses import dataclass
from typing import Callable, Optional
import json, os

GenerateFn = Callable[[str], str]  # prompt -> 대본 텍스트


@dataclass
class SceneCardView:
    scene_no: int
    title: str
    intent_gist: str
    core: str
    core2: Optional[str]
    skin: str

    @classmethod
    def from_row(cls, r: dict) -> "SceneCardView":
        return cls(r["scene_no"], r.get("title", ""), r.get("intent_gist", ""),
                   r.get("core", ""), r.get("core2"), r.get("skin", ""))


@dataclass
class SequenceContext:
    """G1이 기여를 입증한 시퀀스층 캐스케이드 (의도/목표/장애/가치이동/전환/위치/목표분량)."""
    sequence_intent: str
    goal: str
    obstacle: str
    value_from: str
    value_to: str
    turn_type: str
    position: str          # "3/6번째"
    target_chars: int      # 분량 캐스케이드: ep총분량×runtime_share/scene_budget

    @classmethod
    def from_blueprint(cls, s: dict, scene_no: int, ep_total_chars: int) -> "SequenceContext":
        vs = s.get("value_shift", {}) or {}
        mem = s.get("member_scene_nos", [])
        pos = f"{mem.index(scene_no)+1}/{len(mem)}번째" if scene_no in mem else "?"
        tgt = int(ep_total_chars * s.get("runtime_share", 0.08)
                  / max(s.get("scene_budget", len(mem) or 1), 1))
        return cls(s.get("sequence_intent", ""), s.get("goal", ""), s.get("obstacle", ""),
                   vs.get("from", ""), vs.get("to", ""), s.get("turn_type", ""), pos, tgt)

    def render_block(self) -> str:
        return ("[이 씬이 속한 시퀀스]\n"
                f"의도: {self.sequence_intent}\n목표: {self.goal}\n장애: {self.obstacle}\n"
                f"가치이동: {self.value_from} → {self.value_to}\n전환유형: {self.turn_type}\n"
                f"씬 위치: 시퀀스 내 {self.position}\n목표 분량: 약 {self.target_chars}자")


def build_scene_prompt(card: SceneCardView, seq_ctx: Optional[SequenceContext] = None,
                       prev_gist: str = "") -> str:
    """G1 실험과 동일한 프롬프트 계약. seq_ctx=None이면 조건 A(카드만)."""
    extra = ("\n" + seq_ctx.render_block() + "\n") if seq_ctx else "\n"
    return (
        "당신은 한국 드라마 각본가다. 아래 씬 설계 카드만으로(원작 열람 없이) "
        "실제 방송 대본 형식의 씬 하나를 써라. 씬헤딩/지문/대사 형식.\n"
        f"[직전 씬 요지] {prev_gist[:80]}\n"
        "[씬 카드]\n"
        f"씬제목: {card.title}\n의도: {card.intent_gist}\n"
        f"극적기능: {card.core}/{card.core2 or ''}\n장소시간: {card.skin}"
        f"{extra}씬 하나만, 설명 없이 대본만.")


def render_scene(generate: GenerateFn, card: SceneCardView,
                 seq_ctx: Optional[SequenceContext] = None, prev_gist: str = "") -> str:
    return generate(build_scene_prompt(card, seq_ctx, prev_gist))


def load_episode(db_root: str, work_ep: str):
    """seqcard_ko 정본 트리에서 (cards, seqblueprints) 로드."""
    cards = {}
    with open(os.path.join(db_root, "authored", f"{work_ep}.seqcard.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cards[r["scene_no"]] = r
    seqs = []
    p = os.path.join(db_root, "authored_seq", f"{work_ep}.seqblueprint.jsonl")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            seqs = sorted((json.loads(l) for l in f), key=lambda s: s["seq_index"])
    return cards, seqs
