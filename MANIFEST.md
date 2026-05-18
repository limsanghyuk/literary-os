# MANIFEST — Literary OS V571

버전: 7.7.1  
릴리즈일: 2026-05-17  
빌드 타입: Clean Release

## 테스트 결과

| 항목 | 값 |
|------|----|
| PASS | 5,456 |
| FAIL | 0 |
| SKIP | 20 |
| 릴리즈 게이트 | 30/30 PASS |
| 테스트 파일 | 218개 |

## 패키지 구성

```
literary_system/
├── graph_intelligence/     # NKG, 감정 링커, 지식 그래프
├── orchestrators/          # 장편 오케스트레이터
├── longform/               # Fractal Plot Tree
├── predictive/             # PNE (V551~V555)
│   ├── pne_core.py
│   ├── debt_predictor.py
│   ├── preemptive_gate.py
│   └── feedback_learner.py
├── corpus/                 # 외부 코퍼스 브릿지 (V557~V561)
│   ├── corpus_ingestor.py
│   ├── bgem3_embedder.py
│   ├── cim_bootstrap.py
│   └── corpus_validator.py
├── multiwork/              # 다중작품 관리 (V562~V571)
│   ├── multi_work_core.py
│   ├── shared_character_db.py
│   ├── shared_world_db.py
│   ├── genre_transfer.py
│   ├── project_isolation.py
│   ├── multi_work_cim.py
│   ├── author_license_api.py
│   └── multi_work_orchestrator.py
├── adapters_live/          # LLM 어댑터 (Claude / OpenAI / Ollama)
├── gates/                  # 릴리즈 게이트 30종
└── ...
```

## Phase 6 신규 모듈 (V546~V571)

| 버전 | 모듈 | 위치 |
|------|------|------|
| V546 | GraphSyncOrchestrator | graph_intelligence/ |
| V547~V548 | NIL×PBP, LLM0StaticGate, Gate Hierarchy | gates/ |
| V551 | PNECore | predictive/pne_core.py |
| V552 | DebtPredictor | predictive/debt_predictor.py |
| V553 | PreemptiveGate | predictive/preemptive_gate.py |
| V554 | FeedbackLearner | predictive/feedback_learner.py |
| V555 | Gate29 (PNE) | gates/release_gate.py |
| V557 | CorpusIngestor | corpus/corpus_ingestor.py |
| V558 | BGEM3Embedder | corpus/bgem3_embedder.py |
| V559 | CIMBootstrap | corpus/cim_bootstrap.py |
| V560 | CorpusValidator + Gate30 | corpus/corpus_validator.py |
| V562 | MultiWorkCore | multiwork/multi_work_core.py |
| V563 | SharedCharacterDB | multiwork/shared_character_db.py |
| V564 | SharedWorldDB | multiwork/shared_world_db.py |
| V565 | GenreTransferLearning | multiwork/genre_transfer.py |
| V566 | ProjectIsolationManager | multiwork/project_isolation.py |
| V567 | MultiWorkCIM | multiwork/multi_work_cim.py |
| V568 | AuthorLicenseAPI | multiwork/author_license_api.py |
| V570 | MultiWorkOrchestrator | multiwork/multi_work_orchestrator.py |
| V571 | Gate31 (MultiWork) + 릴리즈 | gates/release_gate.py |

## 무결성 파일

- `SHA256SUMS.txt` — literary_system/**/*.py + tests/**/*.py + 루트 설정 파일 체크섬 (652개)
- `RELEASE_INFO.txt` — 릴리즈 메타 정보

## 알려진 제약 (Known Limitations)

**KL-001**: PERSONAL 라이선스에서 `MultiWorkOrchestrator.create_project()` 사용 시 `LicenseViolation`.  
→ COMMERCIAL 이상 라이선스 필요. 설계 의도대로 동작.

**KL-002**: OTel tracer 초기화 테스트 1건 FAIL (V474~, 런타임 비영향).  
→ 별도 Hotfix 사이클 검토 예정.

## 구버전 문서

이전 버전(V328~V546) 문서는 `docs/history/`를 참조하세요.
