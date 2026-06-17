# Literary OS V780

> **판단은 로컬, 생성만 LLM, 학습은 누적**  
> AI 기반 장편 소설·드라마 시나리오 생성 시스템

[![Version](https://img.shields.io/badge/version-13.33.0-blue)]()
[![Tests](https://img.shields.io/badge/tests%20(V780)-11292-brightgreen)]()
[![Phase](https://img.shields.io/badge/RLAIF-loop--C%20GPU%203--mode-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

> **현재 상태**: V780 / v13.33.0 · 테스트 11,292 · **LLM-1 전이 트랙 Exit(V766) + E.4 RLAIF 확장 트랙 Exit(V778)** 완료. 진행 누적: loop-C 폐회로(V774 LoopCClosure·G_LOOPC_WINRATE, ADR-234) · 2축 품질라벨+Critic 판별게이트(V775) · 품질라벨 자동집계(V776) · RunPod 운영 라이프사이클(V777) · 무결성 감사·gates 정리(V779~780). GPU 학습 3-모드(LocalGPUAdapter 4070·ProviderRouter·SplitPipeline·RealRunPodAdapter, ADR-227~233) + 실 DPO 학습 실증(손실↓·보상정확도→1.0, tiny모델). **다음(4트랙)**: T1 실GPU loop-C 라운드(개발자) · T3 생성본체 7-pass L4(★최대 빈칸, 로컬 V781 generation/ 착수·미push) · T2 NextEpisodeBench · T4 공식 Phase E 후반(UI·KEDA·Exit). 잔여: E.3 작가 UI·E.5 배포·E.6 공식 Exit(v14.0.0)는 2단계 후순위. CI(ci_4tier) 녹색 복구(YAML startup·stale 테스트 수정, 2026-06-17). 재검증: `python3 tools/run_release_gate.py` · `python3 tools/generate_test_inventory.py`.

## 빠른 시작

```bash
# 설치
pip install -e ".[dev]"

# 전체 테스트 실행
pytest tests/ -q
# → 9766 passed

# Preflight (RULE-0 의무 — DEV_PROTOCOL_v3.0)
python3 tools/run_preflight.py
# → 13단계 ALL PASS

# 릴리즈 게이트 확인
python3 tools/run_release_gate.py
# → RELEASE GATE PASS: 97 gates passed
```

---

## 시스템 개요

Literary OS는 장편 서사 생성을 위한 AI 파이프라인입니다.  
외부 LLM은 산문 생성에만 선택적으로 사용하며, 플롯·캐릭터·구조 판단은 전부 로컬 모델이 처리합니다 (**LLM-0 원칙**, ADR-015/031).

```
literary_system/
├── sdk/          # PublicSDK v1.0 (SP-C.3) — analyze/repair/predict/generate
├── ensemble/     # AgentCoordinator (Director→Script→Critic→Editor, SP-C.2)
├── agents/       # 멀티에이전트 앙상블 + MultiAgent Coordination (SP-D.2)
├── gates/        # 릴리즈 게이트 97종 (G01~G95 + SP-D Exit)
├── plugins/      # Plugin Registry + Sandbox + Lifecycle (SP-D.3)
├── security/     # ZeroTrust Token + TenantAuthority + Middleware + AuditLog (SP-D.3)
├── chaos/        # Chaos Engineering: Engine/Injector/Scenario/CircuitBreaker/Runner (SP-D.3)
├── ops/          # Observability: OtelSdkAdapter + TraceSampler + Dashboard (SP-D.1)
├── constitution/ # LOSConstitution v2 + Bayesian Opt
├── world/        # PluginRegistry + 5 genre plugins
├── governance/   # ATIAMetadataAuditor
├── graph_intelligence/   # NKG 지식 그래프 + 감정 링커
├── orchestrators/        # 장편 지속 오케스트레이터
├── predictive/           # PNE — 예측적 서사 엔진
├── corpus/               # 외부 코퍼스 브릿지 — BGE-M3 + CIM
├── multiwork/            # 다중작품 관리 오케스트레이터
├── adapters_live/        # LLM 어댑터 (Claude / OpenAI / Ollama)
└── ...           # 83개 패키지 전체 연결 (고립 0, ADR-128)
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
| SP-C.1 | V631~V640 | 자기학습 엔진 / AutoPromotion / SelfLearningMonitor | G62~G63 |
| SP-C.2 | V641~V655 | 멀티에이전트 앙상블 / MAE-MultiWork / SuiteRegistration | G64~G67 |
| SP-C.3 | V656~V665 | PublicSDK v1.0 / OpenAPI / B2B Partner API / Feedback Loop | G68~G71 |
| SP-C.4 | V666~V680 | 경쟁흡수 / DistillationExport / Enterprise SLO / Phase C Exit | G72~G80 |
| SP-D.1 | V681~V695 | Observability Stack (Trace/Sampler/Dashboard/OtelSdk) | G81~G83 |
| SP-D.2 | V696~V710 | MultiAgent Coordination Layer (Bus/Workflow/CircuitBreaker/Supervisor) | G84~G85 |
| **SP-D.3** | **V711~V730** | **Plugin Registry + ZeroTrust + Chaos Engineering** | **G87~G89** |
| **V730** | **v12.4.0** | **SP-D.3 완전 종료 — 88 Gates / 9766+ Tests** | **SP-D3-EXIT ✅** |

---

## 릴리즈 게이트 — 97 PASS

```python
from literary_system.gates.release_gate import GATES
print(len(GATES))  # → 88
```

| 범위 | 게이트 | 내용 |
|------|--------|------|
| G01~G24 | Phase 1~5 | LLM-0 / Arc / RAG / SLM / MultiTenant / RLHF POC |
| G25~G39 | Phase 6 + 거버넌스 | PNE / Corpus / MultiWork / DEV_MODE / AsyncDiscipline |
| G40~G52 | LOSDB + SP-A | SQL/Vector/Graph REAL / E2EProseGate / CLI Exit |
| G53~G61 | SP-B | LoRA Inference / FineTune / PPO / RLHF / Phase B Exit |
| G62~G63 | SP-C.1 | AutoPromotionGate (R≥0.78) / SelfLearningGate (α≥0.70) |
| G64~G67 | SP-C.2 | AgentCoordinator / EnsembleQuality / MAEMultiWork / SuiteRegistration |
| G68~G71 | SP-C.3 | ReaderFeedback / FeedbackLoop / SDKStability / B2BPartner |
| G72~G80 | SP-C.4 | CompetitorAbsorption×5 / DistillationExport / EnterpriseSLO / Revenue / Phase C Exit |
| G81~G83 | SP-D.1 | PreFlightFix / StaticTypeSafety / ObservabilityFoundation |
| G84~G85 | SP-D.2 | AgentCoordinationGate / AgentWorkflowGate |
| **G87** | **SP-D.3** | **Plugin Registry (PR-1~PR-7)** |
| **G88** | **SP-D.3** | **ZeroTrust Security (ZT-1~ZT-7)** |
| **G89** | **SP-D.3** | **Chaos Resilience (CR-1~CR-6)** |

---

## 개발 환경

```bash
# 전체 테스트
pytest tests/ -q  # → 9766 PASS

# Preflight — 각 버전 개발 전 필수 (DEV_PROTOCOL_v3.0 RULE-0)
python3 tools/run_preflight.py  # → 13단계 ALL PASS

# 릴리즈 게이트
python3 tools/run_release_gate.py  # → 97 gates PASS
```

---

## ADR 목록

ADR-001 ~ ADR-191 (`docs/adr/` 디렉터리 참조)

| ADR 범위 | 내용 |
|----------|------|
| ADR-001~097 | Phase 6 → SP-B 전체 |
| ADR-098~128 | SP-C.1~SP-C.4 + G_CONNECTIVITY |
| ADR-129~142 | SP-C.4 안정화 + Phase C Exit |
| ADR-143~157 | SP-D.1 Observability Stack (V681~V695) |
| ADR-158~171 | SP-D.2 MultiAgent Coordination (V696~V710) |
| ADR-172~181 | SP-D.3 Plugin Registry + ZeroTrust (V711~V720) |
| ADR-182~189 | SP-D.3 Auth Bridge + Chaos Engineering (V721~V728) |
| **ADR-190** | **G89 ChaosResilienceGate (V729)** |
| **ADR-191** | **SP-D.3 Exit Gate (V730)** |

---

## 알려진 제약

| ID | 내용 | 영향 |
|----|------|------|
| KL-001 | PERSONAL 라이선스에서 MultiWorkOrchestrator 사용 불가 | 설계 의도. COMMERCIAL 라이선스 필요 |
| KL-002 | OTel tracer 초기화 테스트 1건 SKIP (런타임 비영향) | Release Block 아님 |
| KL-003 | PluginSandbox: RestrictedPython 의존성 필요 (`pip install RestrictedPython`) | G88 ZT-5 PASS 필수 |

---

## 라이선스

MIT License
