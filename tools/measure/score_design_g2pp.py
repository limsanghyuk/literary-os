#!/usr/bin/env python3
"""G2''-C 확정판 결정론 채점기 — 사전등록 고정본 v1.0 (2026-08-05)

목적: 생성된 시퀀스 설계(5필드 텍스트)를 회차 수준 지표로 채점한다.
      "N층의 기여는 N-1층 지표로 잰다"(측정 스코프 원칙)의 확정판 도구.
결정론: 외부 API 없음. 동일 입력 = 동일 출력. 이 파일의 sha256이 사전등록에 고정된다.

입력(JSON 배열): [{"id":..., "model":"gpt-5|claude", "arm":"E|F",
                  "design": "<생성 설계 텍스트>",
                  "actual": {<실제 SequenceBlueprint: turn_type, sequence_intent, goal>}}]
출력: 행별 점수 + (model, arm)별 집계. 주지표 2종:
  (1) turn_match      — 전환유형 일치(실제 작가 turn_type 적중, 0/1)
  (2) intent_proximity — 실제 설계 근접(의도+목표 vs sequence_intent+goal, 문자 2-gram Jaccard)
보조지표: format_complete(5필드 완결) — 게이트용, 판정에 불사용.
"""
import re, json, sys, hashlib

FIELDS = ["의도", "목표", "장애", "가치이동", "전환유형"]

def extract_field(text: str, name: str) -> str:
    m = re.search(rf"{name}\s*[:：]\s*(.+)", text)
    return m.group(1).strip() if m else ""

def _bigrams(s: str):
    s = re.sub(r"\s+", "", s)
    return {s[i:i+2] for i in range(len(s) - 1)}

def jaccard(a: str, b: str) -> float:
    A, B = _bigrams(a), _bigrams(b)
    return len(A & B) / len(A | B) if (A or B) else 0.0

def score(design_text: str, actual_bp: dict) -> dict:
    gen_turn = extract_field(design_text, "전환유형").split()[0].upper() if extract_field(design_text, "전환유형") else ""
    gen_turn = re.sub(r"[^A-Z_]", "", gen_turn)
    actual_turn = str(actual_bp.get("turn_type") or actual_bp.get("turn_class") or "").upper()
    turn_match = 1.0 if (gen_turn and actual_turn and gen_turn == actual_turn) else 0.0
    gen_i = extract_field(design_text, "의도") + " " + extract_field(design_text, "목표")
    act_i = str(actual_bp.get("sequence_intent", "")) + " " + str(actual_bp.get("goal", ""))
    prox = jaccard(gen_i, act_i)
    comp = sum(1 for f in FIELDS if extract_field(design_text, f)) / len(FIELDS)
    return {"turn_match": turn_match, "intent_proximity": round(prox, 4), "format_complete": comp}

def main(path: str):
    rows = json.load(open(path, encoding="utf-8"))
    out, agg = [], {}
    for r in rows:
        s = score(r["design"], r["actual"])
        s.update(id=r.get("id"), model=r.get("model"), arm=r.get("arm"))
        out.append(s)
        agg.setdefault((r.get("model"), r.get("arm")), []).append(s)
    print(f"scorer_sha256={hashlib.sha256(open(__file__,'rb').read()).hexdigest()[:16]}")
    for k in sorted(agg):
        v = agg[k]; n = len(v)
        print(f"{k[0]:>10s} arm={k[1]} n={n:3d}  turn={sum(x['turn_match'] for x in v)/n:.3f}  "
              f"prox={sum(x['intent_proximity'] for x in v)/n:.3f}  comp={sum(x['format_complete'] for x in v)/n:.3f}")
    json.dump(out, open(path + ".scored.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--selftest":
        main(sys.argv[1])
    else:  # 결정론 자가시험
        d = "의도: 진실 접근\n목표: 해영이 단서를 확보한다\n장애: 감시\n가치이동: 의심 → 확신\n전환유형: RISE"
        a = {"turn_type": "RISE", "sequence_intent": "진실에 접근", "goal": "해영이 단서를 확보"}
        s1, s2 = score(d, a), score(d, a)
        assert s1 == s2 and s1["turn_match"] == 1.0 and s1["format_complete"] == 1.0 and s1["intent_proximity"] > 0.5, s1
        print("SELFTEST OK", s1)
