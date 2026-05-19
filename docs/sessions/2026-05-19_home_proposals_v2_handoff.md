# 세션 기록 — 2026-05-19 (집 컴퓨터 / 오후 세션)

## 완료 내용

### 시장 비교 분석 완료
- Sudowrite, Novelcrafter, NovelAI, Squibler, Jenova, NolanAI, AI Screenwriter, Melies vs Literary OS v580 비교
- 자체 ML 레이어 보유: Literary OS + NovelAI 단 두 곳 (나머지 6개 = GPT/Claude API 래퍼)
- NovelAI: Llama 계열 오픈소스 파인튜닝 (Kayra/Clio), 파운데이션 모델 아님
- Novelcrafter: 자체 모델 없음, API 래퍼

### Literary OS 파인튜닝 레이어 확인
- finetune/: FineTuneJobManager(LoRA/QLoRA), ProseStyleDataset(한국 문학 5종), ModelEvalHarness
- learning/: ManuscriptLearner, PhysicsCoefficientUpdater
- corpus/: BGem3Embedder, CorpusIngestor, CIMBootstrap
- pne/: DebtPredictor(RandomForest), FeedbackLearner

### 3인 전문가 협의 — V581+ 장기 로드맵 합의

1차 제안서·설계도 작성 후, 사용자가 v2.0으로 보완함.

**v2.0 12개 보강 사항 (사용자 메타 리뷰):**
- M-01: ChromaDB → Qdrant 우선 채택
- M-02: LOSDB SPOF → PartialAvailability (ADR-058)
- M-03: Constitution v1.0 V585 조기 완성
- M-04: Minimal-CLI V595로 앞당김 (Phase E → Phase A)
- M-05: Multi-backend MigrationManager (SQL/Graph/Vector)
- M-06: MOCK-REAL Equivalence Test (ADR-059)
- M-07: 테스트 목표 V700=7,500 PASS (보수 상향)
- M-08: Llama-3.1-8B(128K) 명시
- M-09: KOFICE/KOCCA 협약 일정 명시 (V583~V594)
- M-10: GPU 비용 SLO $90 soft / $120 hard / $150 emergency
- M-11: BLEU → BERTScore(≥0.85) + LLM-judge(≥4.0) + Style(≥80%)
- M-12: B2B 영업 트랙 V610부터 가동

## V581+ 합의 로드맵 v2.0 요약

| Phase | 버전 | 핵심 목표 | Gate | PASS 목표 |
|-------|------|-----------|------|-----------|
| A | V581~V595 | LOSDB + Qdrant + Constitution + Minimal-CLI | 38→43 | 5,900 |
| B | V596~V610 | 실 LoRA 학습 + KoreanDrama 모델 v1.0 + B2B 영업 | 43→48 | 6,400 |
| C | V611~V630 | RLHF 자가학습 루프 완성 | 48→52 | 7,000 |
| D | V631~V660 | PublicSDK + 경쟁 흡수 5종 + B2B 계약 | 52→55 | 7,500 |
| E | V661+ | CLI 고도화 + 에코시스템 + Phase F~H 장기 비전 | 55+ | 8,000 |

**신규 ADR: ADR-040~060 (21건)**

## 주요 문서 위치 (GitHub)
- 1차 제안서: docs/sessions/literary_os_evolution_proposal_v581.docx (없으면 이 세션서 생성)
- 1차 설계도: docs/sessions/literary_os_evolution_blueprint_v581.docx
- **v2.0 제안서: docs/sessions/literary_os_v581_proposal_v2.docx** ← 최신
- **v2.0 설계도: docs/sessions/literary_os_v581_blueprint_v2.docx** ← 최신

## 다음 개발 시작 절차

1. GitHub에서 `git pull` (main 브랜치)
2. `docs/sessions/literary_os_v581_proposal_v2.docx` + `literary_os_v581_blueprint_v2.docx` 확인
3. Preflight Guide 15단계 수행 (V580 기준선 확인)
4. V581 — SchemaRegistry + Multi-backend MigrationManager 구현 시작

## GitHub 상태 (2026-05-19 오후 기준)
- repo: limsanghyuk/literary-os
- branch: main
- tag: v8.5.0-V580
- 테스트: 5,529+ PASS / Gate 38/38
- CI: 5잡 ALL GREEN
