#!/usr/bin/env python3
"""CT-08A 축자 게이트 — 렌더 120본이 원문 대본을 옮겨 적었는지 정량 검사.

기준(CT-07R 선례 계승): 원문과 **연속 16자 이상 일치 = 차단**.
두 절단면을 모두 보고한다.
  (1) 행 범위 — 원문 한 행 안에서의 연속 일치. 축자 복사의 정직한 계측면.
  (2) 문서 범위 — 공백 제거 후 문서 전체 연결 기준. 행 경계를 넘는 오탐이 섞이므로
      차단 판정에는 쓰지 않고 상한 참고값으로만 보고한다.
프롬프트로 공급된 문자열(블라인드 입력)에서 유래한 일치는 면제.

사용: python CT08A_verbatim_gate.py --run <run_dir> --source <original_extracted/가을동화>
"""
import argparse, json, re, unicodedata
from pathlib import Path

N = 16  # 차단 기준 길이


def norm(s: str) -> str:
    return re.sub(r'\s+', '', unicodedata.normalize('NFC', s))


def grams(s: str, n: int):
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def scan(text: str, gramset, full, supplied):
    """text 안에서 gramset 에 걸리는 구간을 최장 확장하여 수집."""
    hits, i = [], 0
    while i <= len(text) - N:
        if text[i:i + N] in gramset:
            j = i + N
            while j < len(text) and text[i:j + 1] in full:
                j += 1
            seg = text[i:j]
            hits.append({'len': len(seg), 'text': seg[:40],
                         'exempt': seg in supplied})
            i = j
        else:
            i += 1
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--source', required=True)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    run, src = Path(a.run), Path(a.source)

    # 1) 원문 사전 — 행 범위 / 문서 범위
    raw_files = sorted(src.glob('*.txt'))
    lines, doc = [], ''
    for f in raw_files:
        t = f.read_text(encoding='utf-8', errors='ignore')
        lines += [norm(l) for l in t.split('\n')]
        doc += norm(t)
    lines = [l for l in lines if len(l) >= N]
    line_join = '\n'.join(lines)                       # 확장 시 행 경계를 넘지 않게 구분자 삽입
    G_line = set().union(*[grams(l, N) for l in lines]) if lines else set()
    G_doc = grams(doc, N)

    # 2) 프롬프트 공급 문자열(면제 사전)
    supplied = ''
    for d in ('blind_inputs', 'render_inputs'):
        p = run / d
        if p.exists():
            for f in sorted(p.glob('*.md')):
                supplied += norm(f.read_text(encoding='utf-8', errors='ignore')) + '\n'

    # 3) 렌더 검사
    rows, blocked = [], 0
    for f in sorted((run / 'renders').glob('*.out.md')):
        t = norm(f.read_text(encoding='utf-8', errors='ignore'))
        hl = scan(t, G_line, line_join, supplied)
        hd = scan(t, G_doc, doc, supplied)
        nb = [h for h in hl if not h['exempt']]
        if nb:
            blocked += 1
        rows.append({'render': f.name, 'chars': len(t),
                     'max_line_scope': max([h['len'] for h in hl], default=0),
                     'max_line_scope_nonexempt': max([h['len'] for h in nb], default=0),
                     'max_doc_scope': max([h['len'] for h in hd], default=0),
                     'line_hits': hl})

    res = {
        'doc_id': 'LOS-CT08A-VERBATIM-GATE-V1.0',
        'threshold_chars': N,
        'rule': '원문 한 행 안에서 연속 16자 이상 일치 시 차단. 프롬프트 공급 문자열 유래는 면제.',
        'note_doc_scope': ('문서 범위 수치는 공백 제거 후 전 문서를 잇대어 만든 상한 참고값이다. '
                           '서술 끝 + 씬 표제 + 인물명이 붙어 원문 행 경계를 넘는 오탐이 섞이므로 '
                           '차단 판정에 쓰지 않는다.'),
        'source_files': [f.name for f in raw_files],
        'source_lines_ge_threshold': len(lines),
        'source_chars_normalized': len(doc),
        'renders_checked': len(rows),
        'renders_blocked': blocked,
        'max_line_scope_overall': max([r['max_line_scope'] for r in rows], default=0),
        'max_line_scope_nonexempt_overall': max([r['max_line_scope_nonexempt'] for r in rows], default=0),
        'max_doc_scope_overall': max([r['max_doc_scope'] for r in rows], default=0),
        'rows': rows,
    }
    out = Path(a.out) if a.out else run / 'hubsafe' / 'CT08A_VERBATIM_GATE.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"검사 {len(rows)}본 · 차단 {blocked}본 · 행범위 최장 {res['max_line_scope_overall']}자 "
          f"(면제제외 {res['max_line_scope_nonexempt_overall']}자) · 문서범위 상한 {res['max_doc_scope_overall']}자")


if __name__ == '__main__':
    main()
