# 핸드오프 — corpus_ko 실데이터 구축 + 공식 검증 1차 (2026-06-13)

## TL;DR
개발자가 합법 입수한 한국 영화/드라마 대본(`C:\claude\Scripts`)을 작업폴더로 옮겨 **106편 tri-store(ChromaDB+SQLite SceneFeature+NKG)**를 구축하고, **작품별 QC 전수(96/106 클린)** + **공식 검증 4종 실험(FE-7·학습루프·장르곡선·DRSE)**을 실행했다. 데이터 병목 1차 해소 실증.

## ⚠️ verbatim 정책
원문 텍스트(`txt/`,`scenes/`,`chunks/`)·임베딩(`emb_cache`,`chroma_export.tar.gz`)·`scene_features.db`는 **로컬 작업폴더에만 존재, 허브 비커밋**. 허브에는 **코드·리포트·집계 JSON(서사 DNA, verbatim=false)**만 push.

## 파이프라인 (멱등 스크립트)
1. `convert.py` — HWP5→hwp5txt · HWP3/doc/docx→LibreOffice · pdf→pdftotext. 106편 변환.
2. `parse.py` — 씬 파싱(번호헤딩 S#/#/N./씬 + 슬러그 실내·실외·낮·밤 + 폴백블록). 9,744씬.
3. `embed.py` — OpenAI text-embedding-3-small(1536d). 92샤드(재구축 원천).
4. `store_chroma.py` — ChromaDB(ko_scenes 10,837 + ko_slides 7,705). FUSE sqlite 이슈로 로컬빌드→export.
5. `features.py` — SQLite SceneFeature(9,744행: conflict·energy·motif_residue·curiosity·dialogue).
6. `nkg.py` + `llm_chars.py` — NEXT 9,437·인물 836(정규식+LLM-1 grounded)·인물-씬 4,681.
7. `experiments/{meta_gt,run,exp_cbd,exp_d}.py` — 공식 검증 4종.

## QC 전수 (qc_report.json)
96/106 클린. 임베딩 100% 커버. 인물 NO_CHARS=0. 잔여 10편=자막형 전사본(신품 15-20부 등)+반칙왕 과분할(소스 한계).
QC가 잡은 실버그 3건 수정: 파서 무공백 헤딩(광해 10→128) / stale 임베딩 오염(로컬 재빌드) / 인물추출 41편 0명(정규식+LLM 보강).

## 공식 검증 1차 (EXP_REPORT.md) — 정직
- FE-7: 등가중 fitness vs 메타-GT ≈ 우연(0.468). conflict_arc(+0.17)·conflict_mean(+0.16) 정렬 / energy·motif·climax 역상관.
- EXP-D 학습루프: 등가중 0.458 → **LOO-CV 0.640 일반화(과적합 아님)**. 공식은 인간 메타-GT 보정 가능 1차 실증.
- EXP-C: 장르별 긴장곡선 형태 뚜렷 구분(L1 0.286) → T_ideal 장르분리 실증.
- EXP-B: motif_residue 위치상관 0.009 → 현 잔향 정의 약함, 재정의 필요.
- **메타-GT는 잠정(학습지식)**, 개발자 권위데이터로 교체 시 신뢰도 상승.

## 다음 (데이터 보강 시 즉시 재실행)
개발자 권위 acclaim/관객수/장르 라벨 → `meta_gt.py` 교체 후 `run.py`/`exp_d.py` 재실행. 드라마 축 추가. motif_residue·energy/motif/climax 성분 재정의.
