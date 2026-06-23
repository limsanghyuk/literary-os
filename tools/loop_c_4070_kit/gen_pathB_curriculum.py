#!/usr/bin/env python3
# gen_pathB_curriculum.py — SP-E.10 v3 무GPU 하드신호 커리큘럼 생성기
# ------------------------------------------------------------------
# 목적: v2 졸업실패(2R만에 per-token W1=0.976 포화→maintain/rollback, 5연속adopt 구조불가) 해소.
#   chosen=show(감정어 금지) / rejected="능숙하나 평면적" tell(같은 솜씨/길이, show↔tell 축만 차이).
#   라운드↑ = rejected 완성도↑ = gap↓ → base W~0.55에 묶어 라운드마다 조금씩만 이기게(5연속 진짜 adopt).
# I1~I5: per-token 전용/길이매칭8%/verbatim0(상황시드만)/train·held premise-disjoint/토크나이저는 학습단.
# 출력: hardB_held.jsonl(250) + hardB_r1.._r5_train.jsonl(각70). 스키마=트레이너 입력과 동일.
# 사용: set OPENAI_API_KEY=sk-... ; python gen_pathB_curriculum.py --held 250 --per_round 70 --out .
# 이 샌드박스에선 urllib가 행(hang) → curl 서브프로세스 경유. GPU 불요. gpt-4o-mini.
import os, sys, json, glob, random, urllib.request, threading, time, re, argparse, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--held", type=int, default=250)
ap.add_argument("--per_round", type=int, default=70)
ap.add_argument("--rounds", type=int, default=5)
ap.add_argument("--out", default=".")
ap.add_argument("--model", default="gpt-4o-mini")
ap.add_argument("--workers", type=int, default=12)
ap.add_argument("--time_budget", type=float, default=float(os.environ.get("TIME_BUDGET", "1800")))
ap.add_argument("--len_tol", type=float, default=0.08)
ap.add_argument("--self_test", action="store_true")
A = ap.parse_args()

KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OAI_KEY") or ""
if not KEY and not A.self_test:
    sys.exit("OPENAI_API_KEY(또는 OAI_KEY) 미설정. self_test는 키 없이 가능.")

random.seed(20260623)
START = time.time()

SITU_TRAIN = ["재회", "배신 발각", "이별 직전", "비밀 누설", "대치", "고백 직전",
              "상실", "추격 후 정적", "오해", "결별 통보", "재기 결심", "용서를 구함"]
SITU_HELD  = ["귀향", "임종 곁", "첫 만남의 균열", "거래 결렬", "탄로 직전",
              "묵은 빚 청산", "버려진 약속", "마지막 통화"]
GENRES = ["스릴러", "멜로", "수사", "가족", "미스터리", "로맨스", "사극", "의학"]
FUNCS  = ["도입", "상승", "위기", "절정", "전환", "해소"]

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
    "[SHOW] 보여주기: 지문·행동·감각·정적만으로 감정을 *드러내되* 감정을 가리키는 단어(슬픔/분노/두려움/화/외로움 등)는 절대 쓰지 마라.\n"
    "[TELL] 같은 상황·같은 인물·같은 솜씨로 쓰되, 다음 수준의 '말하기'로: {level_desc}\n"
    "제약: 두 버전 모두 320~360자, 동일 분량(글자수 차이 6% 이내), 같은 사건. 군더더기 설명 금지.\n"
    "형식 정확히:\n[SHOW]\n<본문>\n[TELL]\n<본문>"
)

def call(genre, situ, fun, level):
    p = PROMPT.format(genre=genre, situ=situ, fun=fun, level_desc=LEVEL_DESC[level])
    body = json.dumps({"model": A.model,
                       "messages": [{"role": "user", "content": p}],
                       "temperature": 0.85, "max_tokens": 760})
    out = subprocess.run(
        ["curl", "-s", "--max-time", "60",
         "-H", "Authorization: Bearer " + KEY,
         "-H", "Content-Type: application/json",
         "--data-binary", "@-",
         "https://api.openai.com/v1/chat/completions"],
        input=body.encode(), capture_output=True, timeout=70).stdout
    return json.loads(out)["choices"][0]["message"]["content"]

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
    return abs(len(a) - len(b)) / max(len(a), len(b)) <= A.len_tol

EMO_WORDS = re.compile(r"(슬픔|슬프|분노|화가|화났|두려움|무섭|기쁨|행복|외로|불안|절망|그리움|미움|사랑스럽)")
def show_clean(show):
    return len(EMO_WORDS.findall(show)) == 0

def valid(show, tell):
    return (show and tell and 150 <= len(show) and 150 <= len(tell)
            and len_ok(show, tell) and show_clean(show))

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
    caller = mock_call if A.self_test else call
    target = {"held": A.held}
    for r in range(1, A.rounds + 1):
        target["r%d" % r] = A.per_round
    made = {s: count(out_for(s)) for s in target}
    lock = threading.Lock()

    def pending():
        return [s for s in target if made[s] < target[s]]

    def worker():
        while True:
            if time.time() - START > A.time_budget:
                return
            with lock:
                p = pending()
                if not p:
                    return
                split = random.choice(p)
            r = 0 if split == "held" else int(split[1:])
            lv = 3 if split == "held" else round_level(r)
            situ = random.choice(SITU_HELD if split == "held" else SITU_TRAIN)
            genre = random.choice(GENRES); fun = random.choice(FUNCS)
            try:
                show, tell = parse(caller(genre, situ, fun, lv))
            except Exception:
                continue
            if not valid(show, tell):
                continue
            with lock:
                if made[split] >= target[split]:
                    continue
                idx = made[split]
                pid = "%s_%04d" % (split, idx)
                rec = {"pair_id": pid, "work_id": pid, "strategy": "pathB",
                       "chosen": show, "rejected": tell, "level": lv,
                       "genre": genre, "func": fun, "situ": situ, "split": split}
                with open(out_for(split), "a", encoding="utf-8") as o:
                    o.write(json.dumps(rec, ensure_ascii=False) + "\n")
                made[split] += 1

    ts = [threading.Thread(target=worker) for _ in range(A.workers)]
    [t.start() for t in ts]; [t.join() for t in ts]
    print("=== gen_pathB_curriculum 산출 ===")
    for split in ["held"] + ["r%d" % r for r in range(1, A.rounds + 1)]:
        pth = out_for(split)
        lvl = 3 if split == "held" else round_level(int(split[1:]))
        print("  %-18s %3d (target %d)  level=%s" %
              (os.path.basename(pth), count(pth), target.get(split, 0), lvl))

if __name__ == "__main__":
    main()
