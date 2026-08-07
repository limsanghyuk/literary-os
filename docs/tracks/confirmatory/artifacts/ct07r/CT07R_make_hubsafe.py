# -*- coding: utf-8 -*-
"""CT-07R 허브 안전판 생성기 — LOS-CT07R-HUBSAFE-V1.0

허브 경계 정책: "No raw scripts, source scripts, or full authored JSONL"

대상별 처리
  1. 정답표 2본  : evidence 안의 작은따옴표 직접인용을 앞 8자 + 말줄임표로 절단.
                   행 번호·설명 산문·판정 조건·범주·난이도는 원본과 동일하게 보존한다.
                   (CT-06 make_hubsafe.py 선례와 동일 규칙)
  2. 렌더 40본   : 모델 생성물이므로 원문이 아니다. 절단하지 않고 축자 게이트만 건다.
  3. 프롬프트 40본: 후판 팩킷은 이미 허브 봉인분이고 씬 표제는 seqcard 분석 산출물이다.
                   절단하지 않고 축자 게이트만 건다.
  4. 게이트      : 두 작품 원문 행 사전(6자 이상)과 대조하여 일치 건을 전량 보고한다.
                   차단 기준 = 씬 표제를 제외한 16자 이상 일치가 1건이라도 있으면 FAIL.
"""
import json, os, re, glob, hashlib, zipfile

ROOT = '/sessions/compassionate-eager-lovelace/mnt/claude'
RUN  = ROOT + '/CT07R_run_20260807'
OUT  = RUN + '/hubsafe'
os.makedirs(OUT, exist_ok=True)
TRUNC, ELL = 8, '…'
QUOTE = re.compile(r"['‘’\"“”]([^'‘’\"“”]{1,200})['‘’\"“”]")
st = {'n': 0, 'cut': 0, 'before': 0, 'after': 0}

# ---------- 0. 원문 행 사전 ----------
SRC = set()
zf = zipfile.ZipFile(ROOT + '/db/Scripts/한국드라마04/101번째프로포즈.zip')
for nm in zf.namelist():
    if nm.endswith('.txt'):
        raw = zf.read(nm)
        for enc in ('utf-8', 'cp949', 'euc-kr'):
            try:
                t = raw.decode(enc); break
            except Exception:
                continue
        for ln in t.split('\n'):
            s = ln.strip()
            if len(s) >= 6: SRC.add(s)
for p in sorted(glob.glob(ROOT + '/db/corpus_ko/scenes/38사기동대_*.jsonl')) + \
         sorted(glob.glob(ROOT + '/db/corpus_ko/chunks/38사기동대_*.jsonl')):
    for L in open(p, encoding='utf-8'):
        d = json.loads(L)
        for v in d.values():
            if isinstance(v, str) and len(v) > 20:
                for ln in v.split('\n'):
                    s = ln.strip()
                    if len(s) >= 6: SRC.add(s)
print('원문 행 사전 : {:,}행 (6자 이상, 2작)'.format(len(SRC)))

# 프롬프트가 공급한 씬 표제 = 게이트 면제 대상.
# 렌더는 표제 앞에 씬 번호("34. ")를 붙이는 경우가 있고 원문 표제 행도 같은 형태이므로,
# 면제 대조 시 선행 씬 번호를 제거하고 비교한다.
HEADINGS = set()
for p in sorted(glob.glob(RUN + '/render_inputs/*.prompt.md')):
    for ln in open(p, encoding='utf-8'):
        if ln.startswith('씬 표제:'):
            HEADINGS.add(ln.split(':', 1)[1].strip())
print('프롬프트 공급 표제 : {}종 (게이트 면제)'.format(len(HEADINGS)))

NUMPFX = re.compile(r'^\d{1,3}\.\s*')
def is_exempt(L):
    return L in HEADINGS or NUMPFX.sub('', L) in HEADINGS


def redact(s):
    def rep(m):
        q = m.group(1); st['n'] += 1; st['before'] += len(q)
        if len(q) > TRUNC:
            st['cut'] += 1; q = q[:TRUNC] + ELL
        st['after'] += len(q)
        return "'" + q + "'"
    return QUOTE.sub(rep, s)

def scrub(node):
    if isinstance(node, dict):  return {k: scrub(v) for k, v in node.items()}
    if isinstance(node, list):  return [scrub(v) for v in node]
    if isinstance(node, str):   return redact(node)
    return node

def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()

# ---------- 1. 정답표 안전판 ----------
keys = {}
for p in sorted(glob.glob(RUN + '/keys/*.key.json')):
    d = scrub(json.load(open(p, encoding='utf-8')))
    d['_hubsafe'] = {
        'derived_from': os.path.basename(p),
        'source_sha256': sha(p),
        'rule': "evidence 안의 직접인용을 앞 8자 + 말줄임표로 절단. 행 번호·판정 조건·범주·난이도는 원본 동일.",
        'note': '★채점 집행에는 이 파일을 쓰지 말 것. 집행 정본은 로컬 C:\\claude\\CT07R_run_20260807\\keys\\ 이다.',
    }
    keys[os.path.basename(p)] = d
obj = {'doc_id': 'LOS-CT07R-KEY-HUBSAFE-V1.0', 'scale': '0-5',
       'scoring': '5.0 * matched / n_elements', 'keys': keys}
kp = OUT + '/CT07R_KEYS.hubsafe.json'
if os.path.exists(kp): os.remove(kp)
open(kp, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1))
json.load(open(kp, encoding='utf-8'))
print('정답표 안전판 : 인용 {}건 중 {}건 절단  {:,}자 -> {:,}자'.format(
    st['n'], st['cut'], st['before'], st['after']))

# ---------- 2. 축자 게이트 ----------
report = {'dictionary_lines': len(SRC), 'exempt_headings': sorted(HEADINGS), 'targets': {}}
blocked = []
for label, pat in [('renders', RUN + '/renders/*.out.md'),
                   ('render_inputs', RUN + '/render_inputs/*.prompt.md'),
                   ('keys_hubsafe', OUT + '/CT07R_KEYS.hubsafe.json')]:
    hits = []
    files = sorted(glob.glob(pat))
    for p in files:
        t = open(p, encoding='utf-8').read()
        for L in SRC:
            if L in t:
                hits.append({'file': os.path.basename(p), 'len': len(L),
                             'exempt': is_exempt(L), 'text': L})
    hard = [h for h in hits if not h['exempt'] and h['len'] >= 16]
    blocked += hard
    report['targets'][label] = {
        'files': len(files), 'matches': len(hits),
        'max_len_non_exempt': max([h['len'] for h in hits if not h['exempt']] or [0]),
        'blocking_matches_ge16': len(hard),
        'detail': sorted(hits, key=lambda h: -h['len']),
    }
    print('{:16s} 파일 {:3d}  일치 {:3d}  비면제 최장 {:2d}자  차단건 {}'.format(
        label, len(files), len(hits),
        max([h['len'] for h in hits if not h['exempt']] or [0]), len(hard)))
report['verdict'] = 'PASS' if not blocked else 'FAIL'
rp = OUT + '/CT07R_VERBATIM_GATE.json'
if os.path.exists(rp): os.remove(rp)
open(rp, 'w', encoding='utf-8').write(json.dumps(report, ensure_ascii=False, indent=1))
print('★축자 게이트 판정 :', report['verdict'])
