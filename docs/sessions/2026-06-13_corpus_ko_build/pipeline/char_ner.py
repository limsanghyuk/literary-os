#!/usr/bin/env python3
"""
char_ner.py — 시리즈 단위 다중신호 인물 NER (V751, corpus_ko 파이프라인)

설계: docs/sessions/2026-06-13_corpus_ko_build/experiments/CHAR_NER_PROPOSAL.md
8단계: ①시리즈 풀링 ②화자 후보 ③장소 제외 ④재등장 임계
       ⑤형태소(mecab, 선택) ⑥친족/호칭 분리 ⑦LLM 폴백(선택) ⑧NKG char-scene 엣지
원리: "화자 위치 = 강한 인물 신호 / 장소 = 헤딩에만 출현" 분리.
원칙: verbatim 미저장(파생 인물명·엣지만).

실행:
  python char_ner.py --selftest    # 합성 픽스처로 로직 검증(데이터 불요)
  python char_ner.py               # scenes/*.jsonl → char_ner.json (로컬 실데이터)
"""
from __future__ import annotations
import re, sys
from collections import defaultdict, Counter
from typing import Callable, Dict, List, Optional

# ── 장소·호칭 사전 ──
LOCATION_SUFFIX = ("실", "방", "관", "청", "국", "원", "당", "장", "점", "앞", "안", "밖", "옆")
LOCATION_WORDS = {
    "실내", "실외", "낮", "밤", "아침", "저녁", "새벽", "오전", "오후",
    "거실", "안방", "주방", "부엌", "사무실", "병원", "학교", "골목", "도로",
    "길거리", "복도", "옥상", "마당", "정원", "공원", "식당", "카페", "회사",
}
KINSHIP_ROLE = {
    "아버지", "어머니", "아빠", "엄마", "할머니", "할아버지", "형", "누나",
    "오빠", "언니", "동생", "삼촌", "이모", "고모", "아들", "딸", "남편",
    "아내", "부인", "사장", "팀장", "과장", "부장", "회장", "선생", "선생님",
    "교수", "박사", "원장", "실장", "상무", "전무", "검사", "변호사", "형사", "반장",
}


def series_of(work_id: str) -> str:
    """work_id → 시리즈명. 회차 마커(부/회/화/SN/숫자) 제거."""
    s = str(work_id)
    s = re.sub(r'(\d+부|\d+회|\d+화)$', '', s)
    s = re.sub(r'[Ss]\d+$', '', s)
    s = re.sub(r'\d+$', '', s)
    return s.strip() or str(work_id)


def heading_tokens(heading: str) -> set:
    return {t for t in re.split(r'[ .,/#\d]+', heading or "") if t}


def is_location(token: str, h_toks: set) -> bool:
    if token in LOCATION_WORDS or token in h_toks:
        return True
    if len(token) >= 2 and any(token.endswith(suf) for suf in LOCATION_SUFFIX):
        return True
    return False


def speaker_candidates(text: str) -> List[str]:
    """씬 텍스트의 화자 위치 이름 후보 (5포맷: 콜론·탭·단독행·붙음·따옴표앞)."""
    out: List[str] = []
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        m = (re.match(r'^\s*([가-힣]{2,4})\s*[:：\t]', line)      # 이름: / 이름⇥
             or re.match(r'^\s*([가-힣]{2,4})\s*$', line)          # 이름 단독행
             or re.match(r'^\s*([가-힣]{2,4})[\"\'“”(]', line))    # 이름+대사/따옴표
        if m:
            out.append(m.group(1))
    return out


def _mecab_nnp(names, enable: bool = False):
    """⑤ 형태소 보강(mecab NNP 가중) — 미설치 시 무영향(항등)."""
    if not enable:
        return names
    try:
        from mecab import MeCab  # type: ignore
        tagger = MeCab()
        return [n for n in names if any(p.startswith("NNP") for _, p in
                [(t.surface, t.feature.pos) for t in tagger.parse(n)])] or names
    except Exception:
        return names


def extract_cast(
    scenes: List[Dict],
    *,
    min_episodes: int = 2,
    min_count_film: int = 3,
    sparse_threshold: int = 2,
    use_mecab: bool = False,
    llm_fallback: Optional[Callable[[str, List[Dict]], List[str]]] = None,
) -> Dict[str, Dict]:
    """시리즈별 캐스트 추출 (①~④⑥⑦⑧)."""
    by_series: Dict[str, List[Dict]] = defaultdict(list)
    for sc in scenes:                                  # ① 시리즈 풀링
        by_series[series_of(sc["work_id"])].append(sc)

    result: Dict[str, Dict] = {}
    for series, scs in by_series.items():
        episodes = sorted({sc["work_id"] for sc in scs})
        cand_eps: Dict[str, set] = defaultdict(set)
        cand_cnt: Counter = Counter()
        for sc in scs:                                  # ② 화자 후보 + ③ 장소 제외
            h = heading_tokens(sc.get("heading", ""))
            for nm in speaker_candidates(sc.get("text", "")):
                if is_location(nm, h):
                    continue
                cand_eps[nm].add(sc["work_id"])
                cand_cnt[nm] += 1
        roles = sorted(nm for nm in cand_eps if nm in KINSHIP_ROLE)   # ⑥ 호칭 분리
        names = [nm for nm in cand_eps if nm not in KINSHIP_ROLE]
        names = _mecab_nnp(names, use_mecab)                          # ⑤ (선택)

        if len(episodes) >= 2:                          # ④ 재등장 임계
            cast = [n for n in names if len(cand_eps[n]) >= min_episodes]
        else:
            cast = [n for n in names if cand_cnt[n] >= min_count_film]
        cast = sorted(cast, key=lambda n: -cand_cnt[n])

        method = "speaker_ner"
        if len(cast) < sparse_threshold and llm_fallback is not None:  # ⑦ LLM 폴백
            extra = [n for n in (llm_fallback(series, scs) or []) if n not in KINSHIP_ROLE]
            cast = sorted(set(cast) | set(extra), key=lambda n: -cand_cnt.get(n, 0))
            method = "speaker_ner+llm"

        cs_edges = sum(                                 # ⑧ NKG char-scene 엣지
            1 for sc in scs for nm in cast if nm in sc.get("text", ""))
        result[series] = {
            "episodes": episodes, "n_episodes": len(episodes),
            "characters": cast[:20], "n_characters": len(cast),
            "person_roles": roles, "method": method,
            "char_scene_edges": cs_edges,
        }
    return result


# ── 자가검증(합성 픽스처) ──────────────────────────────────────────────────
def _selftest() -> int:
    scenes = [
        {"work_id": "옥탑방고양이1부", "scene_no": 1, "heading": "S#1. 거실. 낮.",
         "text": "정우: 혜련아 어디 가?\n혜련\n나 회사 가.\n안방\n(아버지가 들어온다)\n아버지: 일찍 들어와라."},
        {"work_id": "옥탑방고양이1부", "scene_no": 2, "heading": "S#2. 상무실. 밤.",
         "text": "정우\n오늘 야근이야.\n혜련: 또?\n상무실: (장소 오인 유도)"},
        {"work_id": "옥탑방고양이2부", "scene_no": 1, "heading": "S#1. 거실. 아침.",
         "text": "혜련: 정우야 일어나.\n정우: 응."},
        {"work_id": "곡성", "scene_no": 1, "heading": "S1. 산속.",
         "text": "종구: 뭐여?\n종구: 거기 누구여?\n이삼: 몰라."},
        {"work_id": "곡성", "scene_no": 2, "heading": "S2. 마을.",
         "text": "종구: 가자.\n종구: 빨리."},
    ]
    r = extract_cast(scenes)
    ok = True
    def chk(cond, msg):
        nonlocal ok
        print(("  ✅ " if cond else "  ❌ ") + msg); ok = ok and cond

    # 시리즈 풀링
    chk(set(r.keys()) == {"옥탑방고양이", "곡성"}, f"시리즈 풀링: {sorted(r.keys())}")
    ot = r["옥탑방고양이"]
    chk("정우" in ot["characters"] and "혜련" in ot["characters"], f"드라마 캐스트: {ot['characters']}")
    chk("안방" not in ot["characters"] and "상무실" not in ot["characters"], "장소 누출 차단(안방·상무실)")
    chk("아버지" in ot["person_roles"], f"친족/호칭 분리: {ot['person_roles']}")
    chk(ot["n_episodes"] == 2 and ot["method"] == "speaker_ner", "재등장(2회차)·method")
    gs = r["곡성"]
    chk(gs["characters"] == ["종구"], f"영화 빈도임계(종구 유지, 이삼 제외): {gs['characters']}")
    chk(gs["n_episodes"] == 1, "단일작 처리")
    print("\nSELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _run_pipeline() -> int:
    import json, glob
    scenes = []
    for f in glob.glob("scenes/*.jsonl"):
        for line in open(f, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line:
                scenes.append(json.loads(line))
    cast = extract_cast(scenes, use_mecab=True)
    json.dump(cast, open("char_ner.json", "w"), ensure_ascii=False, indent=0)
    nochar = [s for s, v in cast.items() if v["n_characters"] == 0]
    print(f"시리즈 {len(cast)} · NOCHAR {len(nochar)} → char_ner.json")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else _run_pipeline())
