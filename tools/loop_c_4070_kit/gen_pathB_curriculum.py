#!/usr/bin/env python3
# gen_pathB_curriculum.py — SP-E.10 v3 무GPU 하드신호 커리큘럼 생성기
# ------------------------------------------------------------------
# 목적: SP-E.10 v2 졸업 실패의 실측 원인(2R만에 per-token W1=0.976 포화 → maintain/rollback,
#       5연속 adopt 구조적 불가)을 해소한다. 쉬운 혼합신호(chosen=명작 vs rejected=조잡한 초안)는
#       난도가 너무 커 1~2R에 W=1.0 포화한다. 본 생성기는 *난도를 좁힌* 하드신호를 만든다:
#         chosen   = show(보여주기, 감정어 금지)
#         rejected = "능숙하나 평면적" tell — 같은 솜씨/길이, 오직 show↔tell 축만 다름(작은 마진).
#       라운드가 오를수록 rejected의 완성도를 올려(gap 축소) base W를 ~0.55에 묶어, 라운드마다
#       모델이 *조금씩만* 이길 수 있게 한다 → 5연속 진짜 adopt(W1>W0) 유도.
#
# 검증표준 I1~I5 정합:
#   I1 per-token 전용     : chosen/rejected 길이매칭으로 길이 인공물 차단(아래 charDelta<=8%)
#   I2 길이매칭           : |len(show)-len(tell)| / max <= 0.08, 미달 시 폐기·재생성
#   I3 verbatim 0         : 코퍼스 원문을 직접 넣지 않음(상황 시드만 사용) → 암기 위험 없음
#   I4 작품/프리미스 분리  : held는 train과 *상황 풀이 분리*(premise-disjoint), pair_id 네임스페이스 분리
#   I5 토크나이저 잠금     : 본 생성기는 텍스트만 산출, 학습단에서 잠금
#
# 출력(스키마는 트레이너가 읽는 r*_train/held.jsonl과 동일):
#   {"pair_id","work_id","strategy":"pathB","chosen":<show>,"rejected":<tell>,"level":<1..5>}
#   hardB_held.jsonl (기본 250)  +  hardB_r1.._r5_train.jsonl (기본 각 70)
#
# 사용:
#   set OPENAI_API_KEY=sk-...        (또는 OAI_KEY)
#   python gen_pathB_curriculum.py --held 250 --per_round 70 --out .
# GPU 불요. OpenAI gpt-4o-mini 사용(저비용). 시간예산/재개 지원.
import os, sys, json, glob, random, urllib.request, threading, time, re, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--held", type=int, default=250)
ap.add_argument("--per_round", type=int, default=70)
ap.add_argument("--rounds", type=int, default=5)
ap.add_argument("--out", default=".")
ap.add_argument("--model", default="gpt-4o-mini")
ap.add_argument("--workers", type=int, default=12)
ap.add_argument("--time_budget", type=float, default=float(os.environ.get("TIME_BUDGET", "1800")))
ap.add_argument("--len_tol", type=float, default=0.08)   # I2 charDelta<=8%
ap.add_argument("--self_test", action="store_true", help="API 미과금 오프라인 검증(모킹)")
A = ap.parse_args()

KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OAI_KEY") or ""
if not KEY and not A.self_test:
    sys.exit("OPENAI_API_KEY(또는 OAI_KEY) 미설정. self_test는 키 없이 가능.")

random.seed(20260623)
START = time.time()

# premise-disjoint (I4): train <-> held 상황 풀 분리(교집합 없음)
SITU_TRAIN = ["재회", "배신 발각", "이별 직전", "비밀 누설", "대치", "고백 직전",
              "상실", "추격 후 정적", "오해", "결별 통보", "재기 결심", "용서를 구함"]
SITU_HELD  = ["귀향", "임종 곁", "첫 만남의 균열", "거래 결렬", "탄로 직전",
              "묵은 빚 청산", "버려진 약속", "마지막 통화"]
GENRES = ["스릴러", "멜로", "수사", "가족", "미스터리", "로맨스", "사극", "의학"]
FUNCS  = ["도입", "상승", "위기", "절정", "전환", "해소"]

# 커리큘럼: level↑ = rejected(tell) 완성도↑ = gap↓ = 더 어려움
LEVEL_DESC = {
    1: "감정을 직접 명시하고 설명조로(전형적 tell). 단 문장은 매끄럽게.",
    2: "감정어를 줄이되 여전히 상태를 요약 서술(약한 tell). 지문 약간 포함.",
    3: "행동을 묘사하나 끝에서 감정을 한 번 설명으로 못박음(중간 난도).",
    4: "대체로 보여주되 핵심 감정 1회를 직접 진술(미세한 tell 누설).",
    5: "거의 show에 가깝지만 단 하나의 평면적 요약문이 긴장을 누설(최난도).",
}

def round_level(r):
    return {1: 2, 2: 3, 3: 3, 4: 4, 5: 5}.get(r, 3)

PROMPT = (
    "한국 {genre} 드라마의 한 장면을 두 버전으로 써라. 상황={situ}, 기능={fun}.\n"
    "[SHOW] 보여주기: 지문·행동·감각·정적만으로 감정을 *드러내되* 감정을 가리키는 단어(슬픔/분노/두려움 등)는 절대 쓰지 마라.\n"
    "[TELL] 같은 상황·같은 인물·같은 솜씨로 쓰되, 다음 수준의 '말하기'로: {level_desc}\n"
    "제약: 두 버전 모두 320~360자, 동일 분량(글자수 차이 8% 이내), 같은 사건. 군더더기 설명 금지.\n"
    "형식 정확히:\n[SHOW]\n<본문>\n[TELL]\n<본문>"
)

def call(genre, situ, fun, level):
    p = PROMPT.format(genre=genre, situ=situ, fun=fun, level_desc=LEVEL_DESC[level])
    body = json.dumps({"model": A.model,
                       "messages": [{"role": "user", "content": p}],
                       "temperature": 0.85, "max_tokens": 760}).encode()
    r = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=45))["choices"][0]["message"]["content"]

def parse(t):
    m = re.search(r"\[SHOW\](.*?)\[TELL\](.*)", t, re.S)
    if not m:
        return None, None
    show = re.sub(r"[<>]", "", m.group(1)).strip()[:600]
    tell = re.sub(r"[<>]", "", m.group(2)).strip()[:600]
    return show, tell

def len_ok(a, b):
    if not a or not b:
        return False
    return abs(len(a) - len(b)) / max(len(a), len(b)) <= A.len_tol   # I2

EMO_WORDS = re.compile(r"(슬픔|슬프|분노|화가|두려움|무섭|기쁨|행복|외로|불안|절망|그리움|미움|사랑스럽)")
def show_clean(show):
    return len(EMO_WORDS.findall(show)) == 0

def valid(show, tell):
    return (show and tell and 150 <= len(show) and 150 <= len(tell)
            and len_ok(show, tell) and show_clean(show))

def build_tasks():
    tasks = []
    for i in range(A.held):
        tasks.append(("held", 0, 3, i))
    for r in range(1, A.rounds + 1):
        lv = round_level(r)
        for i in range(A.per_round):
            tasks.append(("r%d" % r, r, lv, i))
    return tasks

def out_for(split):
    return os.path.join(A.out, ("hardB_held.jsonl" if split == "held" else "hardB_%s_train.jsonl" % split))

def count(path):
    return sum(1 for _ in open(path, encoding="utf-8")) if os.path.exists(path) else 0

def mock_call(genre, situ, fun, level):
    base = "그는 문턱에서 멈췄다. 식은 손끝이 문고리를 스치다 떨어졌고, 바닥의 빗물 자국이 길게 번졌다. 멀리서 개가 짖었다. " * 3
    show = (base + "창밖 가로등이 깜빡였다.")[:330]
    if level <= 2:
        tell = ("그는 너무나 슬프고 외로웠다. 마음속 분노가 치밀어 견딜 수 없었다고 그는 느꼈다. " * 5)[:len(show)]
    else:
        tell = (base + "그는 끝내 외로웠다.")[:330]
    if len(tell) < len(show):
        tell = tell + "정" * (len(show) - len(tell))
    else:
        tell = tell[:len(show)]
    return "[SHOW]\n%s\n[TELL]\n%s" % (show, tell)

def main():
    tasks = build_tasks()
    caller = mock_call if A.self_test else call
    target = {}
    for t in tasks:
        target[t[0]] = target.get(t[0], 0) + 1
    made = {s: count(out_for(s)) for s in target}
    lock = threading.Lock()
    cursor = {"i": 0}

    def worker():
        while True:
            if time.time() - START > A.time_budget:
                return
            with lock:
                if cursor["i"] >= len(tasks):
                    return
                split, r, lv, idx = tasks[cursor["i"]]; cursor["i"] += 1
                if made[split] >= target[split]:
                    continue
            situ = random.choice(SITU_HELD if split == "held" else SITU_TRAIN)
            genre = random.choice(GENRES); fun = random.choice(FUNCS)
            try:
                show, tell = parse(caller(genre, situ, fun, lv))
            except Exception:
                continue
            if not valid(show, tell):
                continue
            pid = "%s_%04d" % (split, idx)
            rec = {"pair_id": pid, "work_id": pid, "strategy": "pathB",
                   "chosen": show, "rejected": tell, "level": lv,
                   "genre": genre, "func": fun, "situ": situ, "split": split}
            with lock:
                with open(out_for(split), "a", encoding="utf-8") as o:
                    o.write(json.dumps(rec, ensure_ascii=False) + "\n")
                made[split] += 1

    ts = [threading.Thread(target=worker) for _ in range(A.workers)]
    [t.start() for t in ts]; [t.join() for t in ts]
    print("=== gen_pathB_curriculum 산출 ===")
    for split in ["held"] + ["r%d" % r for r in range(1, A.rounds + 1)]:
        p = out_for(split)
        lvl = 3 if split == "held" else round_level(int(split[1:]))
        print("  %-18s %3d (target %d)  level=%s" %
              (os.path.basename(p), count(p), target.get(split, 0), lvl))

if __name__ == "__main__":
    main()
