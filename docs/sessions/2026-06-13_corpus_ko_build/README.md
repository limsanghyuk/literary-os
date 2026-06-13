# 2026-06-13 corpus_ko 실데이터 구축 + 공식 검증 1차

개발자 합법 입수 한국 영화/드라마 대본 → 106편 tri-store + 작품별 QC 전수 + 공식 검증 4종.

읽는 순서: HANDOFF.md → BUILD_REPORT.md(데이터/QC) → experiments/EXP_REPORT.md(FE-7·학습루프·장르곡선·DRSE).

## ⚠️ verbatim 비커밋
원문 텍스트·임베딩·ChromaDB·SQLite(scene_features.db)는 허브에 없음(로컬 작업폴더 전용).
여기에는 멱등 파이프라인 코드 + 리포트 + 집계 JSON(서사 DNA, verbatim=false)만 포함.
데이터 재구축: pipeline/*.py 순서대로 실행(원천 대본 필요).
