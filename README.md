# Literary OS V680-AUDIT2

> **판단은 로컬, 생성만 LLM, 학습은 누적**  
> AI 기반 장편 소설·드라마 시나리오 생성 시스템

[![Version](https://img.shields.io/badge/version-12.1.0-blue)]()
[![Tests](https://img.shields.io/badge/tests-8845%20PASS-brightgreen)]()
[![Gates](https://img.shields.io/badge/release%20gates-80%2F80%20PASS-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 빠른 시작

```bash
# 설치
pip install -e ".[dev]"

# 전체 테스트 실행
pytest tests/ -q
# → 8845 passed

# 릴리즈 게이트 확인
python -m tools.run_release_gate
# → RELEASE GATE PASS: 80/80 gates passed
```

---

## 시스템 개요

Literary OS는 장편 서사 생성을 위한 AI 파이프라인입니다.  
외부 LLM은 산문 생성에만 선택적으로 사용하며, 플롯·캐릭터·구조 판단은 전부 로컬 모델이 처리합니다 (**LLM-0 원칙**, ADR-015/031).

```
literary_system/
├── sdk/          # PublicSDK v1.0 (SP-C.3) — analyze/repair/predict/generate
├── ensemble/     # AgentCoordinator (Director→Script→Critic→Editor, SP-C.2)
├── agents/       # 멀티에이전트 앙상블 (V646~V653)
├── gates/        # 릴리즈 게이트 80종 (G01~G80)
├── world/        # PluginRegistry + 5 genre plugins
├── governance/   # ATIAMetadataAuditor (V666 통합)
├── ops/          # AdaptiveThrottler + PrometheusExporter + APIReferenceGenerator
├── constitution/ # LOSConstitution v2 + Bayesian Opt
├── graph_intelligence/   # NKG 지식 그래프 + 감정 링커
├── orchestrators/        # 장편 지속 오케스트레이터
├── predictive/           # PNE — 예측적 서사 엔진
├── corpus/               # 외부 코퍼스 브릿지 — BGE-M3 + CIM
├── multiwork/            # 다중작품 관리 오케스트레이터
├── adapters_live/        # LLM 어댑터 (Claude / OpenAI / Ollama)
└── ...           # 76패키지 전체 연결 (고립 0, ADR-128)
```

---

## Phase별 완성 현황

| 단계 | 버전 | 주요 내용 | 게이트 |
| --- | --- | --- | --- |
| Phase 6 | V546~V571 | PNE / CorpusIngestor / MultiWork / AsyncDiscipline | G25~G31 |
| SP-A | V587~V595 | E2EProseGate / GPU SLO / EquivalenceTester / Constitution / CLI | G46~G52 |
| SP-B.1 | V596~V600 | LoRA Fine-tuning Pipeline + HuggingFace | G53~G54 |
| SP-B.2 | V601~V606 | RLHF 루프 / PPO / Reward / ConstitutionAxis | G55~G57 |
| SP-B.3 | V607~V620 | MultiWork 협업 / LoRAStacking / SharedDB | G58~G60 |
| SP-B.4 | V621~V630 | 통합 최적화 / Helm / Monitoring / Phase B Exit | **G61** |
| SP-C.1 | V631~V640 | 자기학습 엔진 / AutoPromotion / SelfLearningMonitor / ContaminationDetector | G62~G63 |
| SP-C.2 | V641~V655 | 멀티에이전트 앙상블 / MAE-MultiWork / SuiteRegistration | G64~G67 |
| SP-C.3 | V656~V665 | PublicSDK v1.0 / OpenAPI / B2B Partner API / Feedback Loop / ModelServing | G68~G71 |
| V666 | V666 | 패키지 연결성 통합 / SDK online 4종 실구현 / ADR-128 | ADR-128 |
| **SP-C.4** | **V667~V680** | **경쟁흡수 / DistillationExport / Enterprise SLO / Revenue / Phase C Exit** | **G72~G79** |
| **V680-AUDIT2** | **v12.1.0** | **Phase C 완전 종료 — 감사 완료** | **전체 80 PASS** |

---

## 릴리즈 게이트 — 80/80 PASS

```python
from literary_system.gates.release_gate import GATES
print(len(GATES))  # → 80
```

| 범위 | 게이트 | 내용 |
|------|--------|------|
| G01~G24 | Phase 1~5 | LLM-0 / Arc / RAG / SLM / MultiTenant / RLHF POC |
| G25~G39 | Phase 6 + 거버넌스 | PNE / Corpus / MultiWork / DEV_MODE / AsyncDiscipline |
| G40~G52 | LOSDB + SP-A | SQL/Vector/Graph REAL / E2EProseGate / CLI Exit |
| G53~G61 | SP-B | LoRA Inference / FineTune / PPO / RLHF / LoRAStacking / Phase B Exit |
| G62~G63 | SP-C.1 | AutoPromotionGate (R≥0.78) / SelfLearningGate |
| G64~G67 | SP-C.2 | AgentCoordinatorGate / EnsembleQualityGate / MAEMultiWorkGate / SuiteRegistrationGate |
| G68~G71 | SP-C.3 | ReaderFeedbackGate / FeedbackLoopGate / SDKStabilityGate / B2BPartnerGate |
| G72~G79 | SP-C.4 | CompetitorAbsorption×5 / DistillationExport / EnterpriseSLO / Revenue / Phase C Exit |
| **G80** | **ADR-128** | **G_CONNECTIVITY — 76패키지 전체 연결 (고립 0)** |

---

## 개발 환경

```bash
# 전체 테스트
pytest tests/ -q  # → 8845 PASS

# Preflight (RULE-0 의무)
python3 tools/run_preflight.py  # → 13단계 ALL PASS

# 릴리즈 게이트
python -m tools.run_release_gate  # → 80/80 PASS
```

---

## ADR 목록

ADR-001 ~ ADR-142 (`docs/adr/` 디렉터리 참조)

| ADR | 내용 |
|-----|------|
| ADR-115 | SuiteRegistrationGate G67 (V655) |
| ADR-116 | PublicSDK v1.0 (V656) |
| ADR-117 | OpenAPI 3.1 Swagger (V657) |
| ADR-118 | B2B Partner API (V658) |
| ADR-119 | ReaderFeedbackCollector G68 (V659) |
| ADR-120 | FeedbackToRLHF Adapter (V660) |
| ADR-121 | Feedback Loop Gate G69 (V661) |
| ADR-122 | ModelServingEndpoint v2.0 (V662) |
| ADR-123 | SDK Stability Gate G70 (V663) |
| ADR-124 | B2B Partner Gate G71 (V664) |
| ADR-125~128 | SP-C.3 완료 + PyPI + Preflight + G_CONNECTIVITY (V665~V666) |
| ADR-129~136 | SP-C.4 경쟁흡수 + DistillationExport + Enterprise + Revenue (V667~V674) |
| ADR-137~142 | SP-C.4 안정화 + Enterprise Gate + Phase C Exit (V675~V680) |

---

## 알려진 제약

| ID | 내용 | 영향 |
|----|------|------|
| KL-001 | PERSONAL 라이선스에서 MultiWorkOrchestrator 사용 불가 | 설계 의도. COMMERCIAL 라이선스 필요 |
| KL-002 | OTel tracer 초기화 테스트 1건 SKIP (런타임 비영향) | Release Block 아님 |

---

## 라이선스

MIT License
