# LOS-CT08A-SCENEIDX-V1.1 — 가을동화 원문 씬 경계 색인
# 16회차 전편에서 헤더 개수 == authored SceneCard 씬 수 임을 검증한 뒤에만 사용한다.
import re

P1 = re.compile(r'^\s*씬\s*(\d{1,3})(?:-\d)?\s*(?=[^\d])')
P2 = re.compile(r'^\s*(\d{1,3})(?:-\d)?\s*(?=[^\d])')
LOC = re.compile(r'[,，/]|낮|밤|아침|저녁|새벽|오후|오전|몽타쥬|연결|외경|황혼')


def norm(s):
    return re.sub(r'\s+', '', s)


def headers(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    raw = []
    for i, l in enumerate(lines, 1):
        s = l.strip()
        for P in (P1, P2):
            m = P.match(s)
            if not m:
                continue
            n = int(m.group(1))
            rest = s[m.end():].strip()
            ok = bool(LOC.search(rest[:30])) or (P is P1 and len(rest) >= 6)
            if 1 <= n <= 200 and len(rest) >= 2 and ok:
                raw.append([i, n, s, norm(rest)])
            break
    hd = []
    for k, r in enumerate(raw):
        nx = raw[k + 1] if k + 1 < len(raw) else None
        if nx and nx[1] == r[1] and nx[3] == r[3] and nx[0] - r[0] <= 15:
            continue
        hd.append((r[0], r[2]))
    return lines, hd


def scene_map(path):
    lines, hd = headers(path)
    return lines, {k + 1: (i, (hd[k + 1][0] - 1) if k + 1 < len(hd) else len(lines), s)
                   for k, (i, s) in enumerate(hd)}
