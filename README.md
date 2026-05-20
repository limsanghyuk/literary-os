# Literary OS V575

> **판단은 로컬, 생성만 LLM, 학습은 누적**  
> AI 기반 장편 소설·드라마 시나리오 생성 시스템

[![Version](https://img.shields.io/badge/version-8.9.0-blue)]()
[![Tests](https://img.shields.io/badge/tests-5564%20PASS-brightgreen)]()
[![Gates](https://img.shields.io/badge/release%20gates-39%2F39%20PASS-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 빠른 시작

```bash
# 설치
pip install -e ".[dev]"

# 전체 테스트 실행
pytest tests/ -q
# → 5456 passed, 20 skipped

# 릴리즈 게이트 확인
python -c "
from literary_system.gates.release_gate import run_release_gate
result = run_release_gate()
print(result['summary'])
"
# → gates_passed: 30/30, status: pass
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
├── gates/                # 릴리즈 게이트 30종 (G01~G31)
├── adapters_live/        # LLM 어댑터 (Claude / OpenAI / Ollama)
└── ...
```

---

## Phase 6 완성 현황

| 단계 | 버전 | 주요 내용 | 게이트 |
|------|------|-----------|--------|
| Stage A (Cleanup) | V546~V548 | ADR-027~031, GraphSync, Gate Hierarchy, LLM0Static | G25~G28 |
| Stage B (PNE) | V551~V555 | PNECore / DebtPredictor / PreemptiveGate / FeedbackLearner | G29 |
| Stage B+ (Corpus) | V557~V561 | CorpusIngestor + BGEM3Embedder + CIMBootstrap | G30 |
| Stage C (MultiWork) | V562~V571 | MultiWorkOrchestrator + SharedCharacterDB + AuthorLicenseAPI | **G31** |

---

## 핵심 패키지 (Phase 6)

### `literary_system/corpus/` — 외부 코퍼스 브릿지
| 모듈 | 역할 |
|------|------|
| `corpus_ingestor.py` | 시나리오 씬 수집 (1만 씬 합성) |
| `bgem3_embedder.py` | BGE-M3 1024-dim 임베딩 |
| `cim_bootstrap.py` | CIM 부트스트랩 |
| `corpus_validator.py` | 라이선스·PII·품질 필터 |

### `literary_system/multiwork/` — 다중작품 관리
| 모듈 | 역할 |
|------|------|
| `multi_work_core.py` | WorkProject FSM, 세션 관리 |
| `shared_character_db.py` | 공유 캐릭터 DB |
| `shared_world_db.py` | 공유 세계관 DB |
| `genre_transfer.py` | 장르 전이 학습 |
| `project_isolation.py` | 프로젝트 격리 관리 |
| `multi_work_cim.py` | 다중작품 CIM |
| `author_license_api.py` | 저자 라이선스 API (PERSONAL / COMMERCIAL) |
| `multi_work_orchestrator.py` | 통합 오케스트레이터 |

---

## 릴리즈 게이트

총 30개 게이트가 전부 통과해야 릴리즈 가능한 설계입니다.

```python
from literary_system.gates.release_gate import run_release_gate
result = run_release_gate()
# {"status": "pass", "gates_passed": 30, "total_gates": 30}
```

| 범위 | 게이트 |
|------|--------|
| G01~G08 | LLM-0 / Arc / Budget / Leakage / Packaging / Pipeline / DRSE / Adapter |
| G09~G16 | StudioAPI / RAG / SLM / Quality / LiveAdapter / SP2Tenant / SP1Adapter / SP4 |
| G17~G24 | SP3Compliance / SP5Ops / ScenePipeline / DramaEpisode / RAGSP2 / SLMSP3 / NIE / NarrativeBlast |
| G25~G31 | CodeCoupling / StoryQuality / PNE / LLM0Static / Corpus / MultiWork |

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
pytest tests/test_v562_v571_multiwork.py -v   # MultiWork (111 tests)
pytest tests/test_v557_v561_corpus.py -v      # Corpus (33 tests)
pytest tests/test_v551_v555_pne.py -v         # PNE
```

---

## ADR 목록

ADR-001 ~ ADR-031 (`docs/` 디렉터리 참조)

---

## 라이선스

MIT License
