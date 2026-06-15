#!/usr/bin/env python3
"""fix_encoding.py — UTF-16 모지바케 일괄 교정 (2026-06-15 remediation)

배경: 일부 소스 .txt가 UTF-16(BOM 0xff 0xfe)인데 utf-8로 읽혀 모지바케(ȯⱸ 등)로
저장됨(112편/코퍼스 25%). NER LLM 폴백이 깨진 이름을 반환해 발견.

원칙: 인코딩만 교정(내용 보존). 한글비율로 최적 디코딩 후보를 선택.
재실행 안전(idempotent): 이미 정상(한글비율 OK)인 파일은 건드리지 않음.

사용: python3 fix_encoding.py /path/to/txt
"""
import sys, glob, os, re

ENCODINGS = ["utf-16", "utf-16-le", "cp949", "utf-8"]

def hangul_ratio(s: str) -> float:
    h = len(re.findall(r"[가-힣]", s))
    t = len(re.sub(r"\s", "", s)) or 1
    return h / t

def readbest(path: str):
    """원시 바이트를 후보 인코딩으로 디코딩, 한글비율 최대(>0.10, 본문>20자)를 채택."""
    raw = open(path, "rb").read()
    best, best_r = None, -1.0
    for enc in ENCODINGS:
        try:
            s = raw.decode(enc, errors="strict")
        except Exception:
            continue
        s = s.replace("﻿", "")
        r = hangul_ratio(s)
        if len(s.strip()) > 20 and r > best_r:
            best, best_r = s, r
    if best is None:  # 모든 strict 실패 → 관대 폴백
        best = raw.decode("utf-8", errors="ignore")
        best_r = hangul_ratio(best)
    return best, best_r

def main(txtdir: str):
    fixed = skipped = 0
    for p in sorted(glob.glob(os.path.join(txtdir, "*.txt"))):
        cur = open(p, "rb").read().decode("utf-8", errors="ignore")
        if len(cur) > 200 and hangul_ratio(cur) >= 0.10:
            skipped += 1
            continue  # 이미 정상
        best, r = readbest(p)
        if r >= 0.10:
            open(p, "w", encoding="utf-8").write(best)
            fixed += 1
            print(f"FIXED {os.path.basename(p)} -> 한글비율 {r:.2f}")
        else:
            print(f"UNRESOLVED {os.path.basename(p)} (best 한글비율 {r:.2f})")
    print(f"\nfixed={fixed} skipped(이미정상)={skipped}")

if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "txt"
    main(d)
