"""
WP-4b (V748) — Pairwise 판정 프로토콜.

§0 금지 준수:
  - 절대 점수로 보상 구성 금지 (G_NO_ABSOLUTE_REWARD)
  - 문체 축 선호 질문 금지 (mode=preference로 문체 판정 불가)
  - 전수 O(n²) 쌍대 금지 (anchor k=5와만 비교 O(kn))

LLM 호출: compare()에서 1콜. cost_cap 필수.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

# ──────────────────────────────────────────────────────────────
# 타입 정의
# ──────────────────────────────────────────────────────────────

try:
    from typing import TypedDict

    class PairwiseJudgment(TypedDict):
        pair_id:       str
        left_id:       str
        right_id:      str
        winner:        Literal["left", "right"]
        mode:          Literal["preference", "trait", "canon_proximity"]
        trait:         Optional[str]      # mode=trait일 때 판단 기준
        rationale:     str                # R5 근거 (의무)
        judge_id:      str                # 모델+페르소나+temp
        position_seed: int                # 위치 무작위 재현용

except ImportError:
    PairwiseJudgment = dict  # type: ignore[misc,assignment]

# ──────────────────────────────────────────────────────────────
# Anchor Set v1 (sha256 고정, 교체 시 ADR 의무)
# PD 명작 5씬 식별자 — 실 DB 없는 환경에서 fallback ID 사용
# ──────────────────────────────────────────────────────────────

ANCHOR_SET_V1: List[str] = [
    "운수좋은날_s02",
    "운수좋은날_s10",
    "운수좋은날_s11",
    "pd_anchor_s01",
    "pd_anchor_s02",
]

# anchor set sha256 (내용이 아닌 ID 목록의 해시 — 교체 감지용)
_ANCHOR_IDS_SHA256 = hashlib.sha256(
    json.dumps(ANCHOR_SET_V1, ensure_ascii=False).encode()
).hexdigest()

DEFAULT_JUDGE = "gpt-4o:persona_balanced:temp0"
_TIEBREAK_THRESHOLD = 0.3   # |Δ| < 0.3 → 박빙 → 양방향 2판정

# ──────────────────────────────────────────────────────────────
# 내부 유틸
# ──────────────────────────────────────────────────────────────

def _load_scene_text(scene_id: str, db: Any) -> Optional[str]:
    """
    DB(SQLite 경로 str 또는 dict 픽스처)에서 씬 텍스트 반환.
    DB가 dict면 fixture 모드.
    """
    if isinstance(db, dict):
        return db.get(scene_id)

    try:
        import sqlite3
        con = sqlite3.connect(str(db))
        row = con.execute(
            "SELECT synopsis FROM scene WHERE scene_id=?", (scene_id,)
        ).fetchone()
        con.close()
        return row[0] if row else None
    except Exception:
        return None


def _call_llm(
    prompt: str,
    judge_id: str,
    cost_cap: float,
) -> Tuple[str, str]:
    """
    LLM 판정 호출. 실제 호출 또는 테스트 mock.
    반환: (winner_side "left"|"right", rationale)
    """
    # cost_cap 사전 확인
    estimated_cost = 0.002   # 1콜 추정 (gpt-4o, ~500 tokens)
    if estimated_cost > cost_cap:
        raise ValueError(
            f"cost_cap {cost_cap:.4f} < 추정 비용 {estimated_cost:.4f} — 중단"
        )

    model, _, temp_str = judge_id.split(":")
    temperature = float(temp_str.replace("temp", ""))

    try:
        import openai
        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        raw = resp.choices[0].message.content or ""
        # 간단 파서: 첫 단어가 "left"/"right" 또는 내용 기반
        winner: str = "left"
        for token in raw.lower().split():
            if token in ("left", "right"):
                winner = token
                break
        return winner, raw.strip()

    except ImportError:
        raise RuntimeError(
            "openai 패키지 미설치. pip install openai 후 재실행."
        )
    except Exception as exc:
        raise RuntimeError(f"LLM 호출 실패 ({judge_id}): {exc}") from exc


def _build_prompt(
    left_text: str,
    right_text: str,
    mode: str,
    trait: Optional[str],
    position_seed: int,
) -> Tuple[str, bool]:
    """
    비교 프롬프트 생성.
    mode=preference + 문체 판단 → 금지 (D-PW3).
    반환: (prompt_str, swapped)
    """
    if mode == "preference" and trait and any(
        kw in trait for kw in ["문체", "스타일", "style", "tone"]
    ):
        raise ValueError(
            "D-PW3 위반: 문체 축 판단은 mode='trait'만 허용. "
            "preference 모드에서 문체 선호 질문 금지."
        )

    rng = random.Random(position_seed)
    swap = rng.random() > 0.5

    if swap:
        a_text, b_text = right_text, left_text
        a_label, b_label = "right", "left"
    else:
        a_text, b_text = left_text, right_text
        a_label, b_label = "left", "right"

    if mode == "trait":
        criterion = f"'{trait}' 특성을 더 잘 구현한 씬"
    elif mode == "canon_proximity":
        criterion = "명작 문학의 문체·구조적 특성에 더 가까운 씬"
    else:
        criterion = "전반적으로 더 문학적 완성도가 높은 씬"

    prompt = (
        f"두 씬 중 {criterion}을 선택하세요. "
        f"반드시 'left' 또는 'right'로만 답하고 간략한 근거를 제시하세요.\n\n"
        f"[left]\n{a_text[:800]}\n\n"
        f"[right]\n{b_text[:800]}"
    )
    return prompt, swap


# ──────────────────────────────────────────────────────────────
# 공개 API
# ──────────────────────────────────────────────────────────────

def compare(
    a_id:       str,
    b_id:       str,
    db:         Any,
    mode:       Literal["preference", "trait", "canon_proximity"] = "preference",
    trait:      Optional[str] = None,
    judge:      str = DEFAULT_JUDGE,
    cost_cap:   float = 0.05,
) -> PairwiseJudgment:
    """
    두 씬을 쌍대 비교. LLM 1콜.

    a_id, b_id: scene_id (DB에서 텍스트 조회)
    db:         SQLite 경로(str/Path) 또는 {scene_id: text} 픽스처 dict
    mode:       preference | trait | canon_proximity
    trait:      mode=trait일 때 판단 기준 명세 (예: '절제 저온 문체')
    judge:      "model:persona:tempN" 형식
    cost_cap:   비용 상한 USD
    """
    a_text = _load_scene_text(a_id, db)
    b_text = _load_scene_text(b_id, db)

    if a_text is None:
        raise ValueError(f"씬 미발견: {a_id}")
    if b_text is None:
        raise ValueError(f"씬 미발견: {b_id}")

    seed = random.randint(0, 2**31)
    prompt, swapped = _build_prompt(a_text, b_text, mode, trait, seed)
    raw_winner, rationale = _call_llm(prompt, judge, cost_cap)

    # swap 역변환
    if swapped:
        winner = "right" if raw_winner == "left" else "left"
    else:
        winner = raw_winner

    return PairwiseJudgment(  # type: ignore[call-arg]
        pair_id       = f"{a_id}_vs_{b_id}",
        left_id       = a_id,
        right_id      = b_id,
        winner        = winner,
        mode          = mode,
        trait         = trait,
        rationale     = rationale,
        judge_id      = judge,
        position_seed = seed,
    )


def tournament(
    ids:     List[str],
    db:      Any,
    anchors: Optional[List[str]] = None,
    k:       int = 5,
    mode:    Literal["preference", "trait", "canon_proximity"] = "preference",
    trait:   Optional[str] = None,
    judge:   str = DEFAULT_JUDGE,
    cost_cap: float = 1.0,
) -> List[PairwiseJudgment]:
    """
    anchor set k개와만 비교 O(kn) — 전수 O(n²) 금지.
    judgments 반환. bt_scores()에 입력 가능.
    """
    used_anchors = (anchors or ANCHOR_SET_V1)[:k]
    judgments: List[PairwiseJudgment] = []

    per_call = 0.003
    budget = cost_cap

    for scene_id in ids:
        if scene_id in used_anchors:
            continue
        for anchor_id in used_anchors:
            if budget < per_call:
                sys.stdout.write(
                    f"[tournament] cost_cap 소진 — {len(judgments)}판정 후 중단\n"
                )
                return judgments
            try:
                j = compare(
                    a_id     = scene_id,
                    b_id     = anchor_id,
                    db       = db,
                    mode     = mode,
                    trait    = trait,
                    judge    = judge,
                    cost_cap = per_call,
                )
                judgments.append(j)
                budget -= per_call
            except Exception as exc:  # noqa: BLE001
                sys.stdout.write(f"[tournament] 스킵 {scene_id} vs {anchor_id}: {exc}\n")

    return judgments


def bt_scores(judgments: List[Any]) -> Dict[str, float]:
    """
    Bradley-Terry 잠재 점수 추정 (반복 MLE).
    기존 절대 임계 게이트와 호환 계층 (P-6).
    반환: {scene_id: bt_score}
    """
    if not judgments:
        return {}

    # 참가자 수집
    players: set = set()
    wins: Dict[str, Dict[str, int]] = {}   # wins[i][j] = i가 j를 이긴 횟수

    for j in judgments:
        left_id  = j["left_id"]  if isinstance(j, dict) else j.left_id
        right_id = j["right_id"] if isinstance(j, dict) else j.right_id
        winner   = j["winner"]   if isinstance(j, dict) else j.winner
        players.add(left_id)
        players.add(right_id)
        wins.setdefault(left_id,  {}).setdefault(right_id, 0)
        wins.setdefault(right_id, {}).setdefault(left_id,  0)
        if winner == "left":
            wins[left_id][right_id]  += 1
        else:
            wins[right_id][left_id]  += 1

    # BT 반복 MLE (최대 200 iter)
    scores: Dict[str, float] = {p: 1.0 for p in players}
    for _ in range(200):
        new_scores: Dict[str, float] = {}
        for i in players:
            numer = sum(wins[i].get(j, 0) for j in players if j != i)
            denom = sum(
                (wins[i].get(j, 0) + wins[j].get(i, 0)) / (scores[i] + scores[j])
                for j in players
                if j != i and (wins[i].get(j, 0) + wins[j].get(i, 0)) > 0
            )
            new_scores[i] = numer / denom if denom > 0 else scores[i]
        # 정규화
        total = sum(new_scores.values()) or 1.0
        new_scores = {k: v / total for k, v in new_scores.items()}
        if max(abs(new_scores[p] - scores[p]) for p in players) < 1e-6:
            scores = new_scores
            break
        scores = new_scores

    return scores


def transitivity_check(judgments: List[Any]) -> float:
    """
    판정 그래프 순환률 (Kendall τ 기반 추정).
    G_TRANSITIVITY 임계: < 5%.
    반환: 순환률 (0.0 ~ 1.0)
    """
    if len(judgments) < 3:
        return 0.0

    # 방향 그래프: edges[i] = {j: i가 j를 이김}
    edges: Dict[str, set] = {}
    for j in judgments:
        left_id  = j["left_id"]  if isinstance(j, dict) else j.left_id
        right_id = j["right_id"] if isinstance(j, dict) else j.right_id
        winner   = j["winner"]   if isinstance(j, dict) else j.winner
        edges.setdefault(left_id,  set())
        edges.setdefault(right_id, set())
        if winner == "left":
            edges[left_id].add(right_id)
        else:
            edges[right_id].add(left_id)

    players = list(edges.keys())
    n = len(players)
    if n < 3:
        return 0.0

    # 3-사이클 탐지
    cycles = 0
    triples = 0
    for i in range(n):
        for j in range(n):
            if j == i:
                continue
            if players[j] not in edges[players[i]]:
                continue
            for k in range(n):
                if k == i or k == j:
                    continue
                if players[k] not in edges[players[j]]:
                    continue
                triples += 1
                if players[i] in edges[players[k]]:   # i→j→k→i 순환
                    cycles += 1

    return cycles / triples if triples > 0 else 0.0


def get_anchor_sha() -> str:
    """Anchor set v1 ID 목록의 sha256 반환 (변경 감지용)."""
    return _ANCHOR_IDS_SHA256
