# -*- coding: utf-8 -*-
"""CT-03 허브 안전판 — LOS-CT-HUBSAFE-CT03-20260805-V1.0

RESULT_rows.json 의 `reason` 은 채점자가 판단 근거로 원문/렌더를 직접 인용한다.
원작 조건(H)의 인용은 대본 원문이므로 허브 경계에 걸린다.
따옴표 인용을 8자로 절단하고, 원문 행 사전으로 2차 방어한다.
items_raw.json·packets/·items/ 는 원문 전문을 담으므로 허브에 올리지 않는다.
"""
import json, os, re, argparse, hashlib

ap = argparse.ArgumentParser()
ap.add_argument('--root', default=r'C:\claude')
A = ap.parse_args()
R = A.root
CT03 = os.path.join(R, 'CT03_run_20260805')
OUT = os.path.join(R, 'CT_AUDIT_20260805', 'hubsafe')
os.makedirs(OUT, exist_ok=True)
TRUNC, ELL = 8, '…'
QUOTE = re.compile(r"['‘’\"“”]([^'‘’\"“”]{1,200})['‘’\"“”]")
st = {'n': 0, 'cut': 0, 'line': 0}

items = json.load(open(os.path.join(CT03, 'items_raw.json'), encoding='utf-8'))
SRC = set()
for it in items:
    for ln in it['H'].split('\n'):          # H = 원작 원문. A/B 는 생성물.
        t = ln.strip()
        if len(t) >= 6:
            SRC.add(t)
ORIG = os.path.join(R, 'G1_run_20260804', 'orig')
for fn in sorted(os.listdir(ORIG)):
    if fn.endswith('.txt'):
        for ln in open(os.path.join(ORIG, fn), encoding='utf-8'):
            t = ln.strip()
            if len(t) >= 6:
                SRC.add(t)
ORDER = sorted(SRC, key=len, reverse=True)


def rq(m):
    q = m.group(1)
    st['n'] += 1
    if len(q) > TRUNC:
        st['cut'] += 1
        q = q[:TRUNC] + ELL
    return "'" + q + "'"


def scrub(s):
    s = QUOTE.sub(rq, s)
    for L in ORDER:
        if L in s:
            st['line'] += 1
            s = s.replace(L, L[:TRUNC] + ELL)
    return s


rows = json.load(open(os.path.join(CT03, 'RESULT_rows.json'), encoding='utf-8'))
for r in rows:
    if isinstance(r.get('reason'), str):
        r['reason'] = scrub(r['reason'])
obj = {
    'doc_id': 'LOS-CT-03-RESULT-ROWS-HUBSAFE',
    'derived_from': 'RESULT_rows.json',
    'source_sha256': hashlib.sha256(open(os.path.join(CT03, 'RESULT_rows.json'), 'rb').read()).hexdigest(),
    'rule': "reason 안의 따옴표 인용을 앞 8자로 절단 + 원문 행 사전 2차 방어. 판정·점수·5차원은 원본과 동일.",
    'n': len(rows), 'rows': rows,
}
p = os.path.join(OUT, 'CT03_RESULT_rows.hubsafe.json')
if os.path.exists(p):
    os.remove(p)
open(p, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=2))
json.load(open(p, encoding='utf-8'))

hits = [L for L in SRC if L in open(p, encoding='utf-8').read()]
print('CT-03 rows 안전판 : {:,} B  n={}'.format(os.path.getsize(p), len(rows)))
print('  인용 {}건 중 {}건 절단, 2차 방어 {}건'.format(st['n'], st['cut'], st['line']))
print('  원문 행 사전 {}행 (items_raw H + G1 orig)'.format(len(SRC)))
print('  ★게이트 원문 행 완전일치 : {}건 -> {}'.format(len(hits), 'PASS' if not hits else '★FAIL ' + repr(hits[:3])))
