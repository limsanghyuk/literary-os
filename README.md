# Literary OS V612

> **판단은 로컬, 생성만 LLM, 학습은 누적**  
> AI 기반 장편 소설·드라마 시나리오 생성 시스템

[![Version](https://img.shields.io/badge/version-10.17.0-blue)]()
[![Tests](https://img.shields.io/badge/tests-6527%20PASS-brightgreen)]()
[![Gates](https://img.shields.io/badge/release%20gates-58%2F58%20PASS-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 빠른 시작

```bash
# 설치
pip install -e ".[dev]"

# 전체 테스트 실행
pytest tests/ -q
# → 6321+ passed (V604 기준)

# 릴리즈 게이트 확인
python -c "
from literary_system.gates.release_gate import run_release_gate
result = run_release_gate()
print(result['summary'])
"
# → RELEASE GATE PASS: 54/54 gates passed
```

---

## 시스템 개요

Literary OS는 장편 서사 생성을 위한 AI 파이프라인입니다.  
외부 LLM은 산문 생성에만 선택적으로 사용하며, 플롯·캐릭터·구조 판단은 전부 로컬 모델이 처리합니다 (**LLM-0 원칙**, ADR-015/031).

```
literary_system/
├── graph_intelligence/   # NKG 지식 그래프 + 감정 링커
├── orchestrators/        # 장편 지속 오케스트레이터
├── predictive/           # PNE — 예측적 서사 엔진 (V551~V555)
├── corpus/               # 외부 코퍼스 브릿지 — BGE-M3 + CIM (V557~V561)
├── multiwork/            # 다중작품 관리 오케스트레이터 (V562~V571)
├── db/                   # LOSDB — SQL/Vector/Graph 스토리지 + Facade (V581~V586)
├── gates/                # 릴리즈 게이트 51종 (G01~G55)
├── adapters_live/        # LLM 어댑터 (Claude / OpenAI / Ollama)
└── ...
```

---

## 릴리즈 이력 요약

| 단계 | 버전 | 주요 내용 | 게이트 |
|------|------|-----------|--------|
| Phase 6 Stage A | V546~V548 | ADR-027~031, GraphSync, Gate Hierarchy, LLM0Static | G25~G28 |
| Phase 6 Stage B | V551~V555 | PNECore / DebtPredictor / PreemptiveGate / FeedbackLearner | G29 |
| Phase 6 Stage B+ | V557~V561 | CorpusIngestor + BGEM3Embedder + CIMBootstrap | G30 |
| Phase 6 Stage C | V562~V571 | MultiWorkOrchestrator + SharedCharacterDB + AuthorLicenseAPI | **G31** |
| 거버넌스 | V575~V580 | DEV_MODE 보안패치 / Logging / 어댑터 캐노니컬 / AsyncDiscipline | G32~G39 |
| LOSDB Phase A | V581 | SchemaRegistry + MigrationManager (SQL/Vector/Graph Mock) | G40 |
| LOSDB Phase B | V582~V585 | SQLiteRealAdapter / MigrationEngine / VectorRealAdapter / GraphRealAdapter | G41~G44 |
| LOSDB Phase C | **V586** | **LOSDBClient Facade + cross_query + query_by_label** | **G45** |
| V587 품질 강화 | **V587** | **E2EProseGate + Gate 계층화(L0~L3) + ADR-046~048** | **G46** |
| 품질 기반 강화 | **V587** | **ADR-048 Doc Consistency CI + 정합성 6파일 검사 + Release 자동화** | **G46** |

---

## LOSDB 구조 (V586 기준)

| 레이어 | Mock | REAL |
|--------|------|------|
| SQL | V581 ✅ | V582 ✅ |
| Vector | V581 ✅ | V584 ✅ |
| Graph | V581 ✅ | V585 ✅ |
| **Facade** | — | **V586 ✅** |

```python
from literary_system.db import LOSDBClient, LOSDBClientRecord
from literary_system.db.sql_real_adapter import SQLiteRealAdapter
from literary_system.db.vector_real_adapter import VectorRealAdapter
from literary_system.db.graph_real_adapter import GraphRealAdapter

client = LOSDBClient(
    sql=SQLiteRealAdapter(db_path=":memory:"),
    vector=VectorRealAdapter(dim=128),
    graph=GraphRealAdapter(),
)
results = client.cross_query(["sql", "vector", "graph"], label="chapter_01")
```

---

## 릴리즈 게이트

총 **45개** 게이트가 전부 통과해야 릴리즈 가능한 설계입니다.

```python
from literary_system.gates.release_gate import run_release_gate
result = run_release_gate()
# {"status": "pass", "gates_passed": 45, "total_gates": 45}
```

| 범위 | 게이트 |
|------|--------|
| G01~G08 | LLM-0 / Arc / Budget / Leakage / Packaging / Pipeline / DRSE / Adapter |
| G09~G16 | StudioAPI / RAG / SLM / Quality / LiveAdapter / SP2Tenant / SP1Adapter / SP4 |
| G17~G24 | SP3Compliance / SP5Ops / ScenePipeline / DramaEpisode / RAGSP2 / SLMSP3 / NIE / NarrativeBlast |
| G25~G31 | CodeCoupling / StoryQuality / PNE / LLM0Static / Corpus / MultiWork / (AsyncDiscipline) |
| G32~G39 | LoggingDiscipline / SchemaRoundTrip / AuthRegression / AdapterCanonical / GateRegistry / DuplicateZero / AsyncDiscipline / PerformanceBaseline |
| G40~G46 | DBMigration / SQLRealAdapter / MigrationEngine / VectorRealAdapter / GraphRealAdapter / LOSDBClient / **E2EProseGate** |

---

## 알려진 제약

| ID | 내용 | 영향 |
|----|------|------|
| KL-001 | PERSONAL 라이선스에서 MultiWorkOrchestrator 사용 불가 (`LicenseViolation`) | 설계 의도. COMMERCIAL 라이선스 필요 |
| KL-002 | OTel tracer 초기화 테스트 1건 FAIL (V474~, 런타임 비영향) | Release Block 아님 |

---

## 개발 환경

```bash
# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 특정 패키지 테스트
pytest tests/test_v586_losdb_client.py -v      # LOSDBClient Facade
pytest tests/e2e/ -v -m 'not real_llm'          # E2E ProseGate G46 (45 tests)
pytest tests/test_v585_graph_real_adapter.py -v # GraphRealAdapter
pytest tests/test_v584_vector_real_adapter.py -v # VectorRealAdapter
pytest tests/test_v582_sql_real_adapter.py -v   # SQLiteRealAdapter
pytest tests/test_v562_v571_multiwork.py -v    # MultiWork (111 tests)
pytest tests/test_v557_v561_corpus.py -v       # Corpus (33 tests)
pytest tests/test_v551_v555_pne.py -v          # PNE
```

---

## ADR 목록

ADR-001 ~ ADR-048 (`docs/adr/` 디렉터리 참조)

---

## 라이선스

MIT License
