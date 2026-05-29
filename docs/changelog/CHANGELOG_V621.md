# CHANGELOG — V621 (v10.26.0)

**릴리즈 날짜**: 2026-05-25  
**버전**: 10.25.2 → 10.26.0  
**ADR**: ADR-088  
**Phase**: B · SP-B.2 retrofit P-IF 3건

---

## V621-PRE — 자동 학습 강제 (Rule-9 추가)

### AGENTS.md
- 상단에 `🔴 필수 학습 (Critical Loading)` 블록 추가
- v3 핸드오프 3파일 미로드 시 코드 작성 금지 조건 명문화

### tools/preflight_step15.py
- `REQUIRED_V3_FILES` 상수 추가 (핸드오프 .md 2개)
- `verify_v3_handoff() -> dict` 함수 추가
- `check_v3_handoff() -> list[Violation]` Rule-9 (HIGH) 추가
- `Violation` NamedTuple에 `code: str = ""` 선택 필드 추가
- `main()` Section C에 `check_v3_handoff()` 연결
- **+5 TC** (tests/unit/test_v621_pre_handoff.py)

---

## V621 — SP-B.2 retrofit P-IF 3건 (ADR-088)

### P-IF-01: AgentEnvelope + RoutingPolicy 4축

**literary_system/llm_bridge/agent_envelope.py** (신규)
- `AgentRole` Enum 5종: SCENE_WRITER / CRITIC / EDITOR / HISTORIAN / READER_VOICE
- `AgentEnvelope` dataclass: agent_id, role, prompt, context, parent_agent_id, session_id, metadata
- `RoutingDecision` Enum: LOCAL_LORA / EXTERNAL_LLM / CASCADE
- `RoutingPolicy` dataclass: 4축 가중치(cost/latency/quality/role) 합계 1.0 강제 + `decide_for_agent()`

**literary_system/llm_bridge/canonical_bridge_v2.py** (확장)
- `_bridge_generate_with_envelope()` 추가: str/AgentEnvelope 이중 입력 래퍼
- `__all__` AgentEnvelope/AgentRole/RoutingDecision/RoutingPolicy 재노출

### P-IF-03: ReaderFeedbackIngest

**literary_system/multiwork/reader_feedback_ingest.py** (신규)
- `ReaderFeedback` frozen dataclass: rating 1~5 검증, timestamp UTC 자동설정, `to_dict()`
- `RewardSignal` dataclass
- `RewardSignalAdapter` @runtime_checkable Protocol
- `ReaderFeedbackIngest`: Phase B=NotImplementedError, Phase C+=adapter 주입 활성화
  - `ingest()`, `is_phase_c_active()`, `ingested_count()`, `recent_history()`, `summary()`
- `PHASE_C_FEATURE: bool = True` 상수

### P-IF-04: OpenAPI SemVer

**literary_system/serving/model_serving_endpoint.py** (확장)
- `SEMVER_MAJOR=1 / SEMVER_MINOR=0 / SEMVER_PATCH=0 / SEMVER="1.0.0"` 상수
- `_OPENAPI_SCHEMA_MINIMAL`: OpenAPI 3.1 스키마 딕셔너리
- `get_api_version_response()`: `{"semver": SEMVER}` 반환
- `get_openapi_schema()`: 스키마 딕셔너리 반환
- `build_app_with_semver()`: FastAPI + /openapi.yaml + /api_version 엔드포인트

**tools/detect_openapi_breaking.py** (신규)
- SEMVER_MAJOR 기준 브레이킹 체인지 탐지
- `--baseline MAJOR` (기본 1), `--warn-only` CI 관대 모드
- exit(0)=정상 / exit(1)=브레이킹

**tools/export_openapi.py** (신규)
- `--format yaml|json`, `--output PATH` 옵션

**.github/workflows/openapi_diff.yml** (신규)
- model_serving_endpoint.py 또는 detect_openapi_breaking.py 변경 시 트리거
- Phase B: `--warn-only` (CI 미차단)

### 테스트
- **tests/unit/test_v621_pre_handoff.py**: 5 TC (V621-PRE)
- **tests/unit/test_v621_sp_b2_retrofit.py**: 60 TC (ADR-088 전체)
- **+65 TC** | 누적 6,801 TC

### ADR
- **docs/adr/ADR-088.md**: SP-B.2 retrofit P-IF 3건 통합 결정

---

## 회귀 검증

- 단위 테스트 643/643 PASS
- G56/G57 회귀 0건
- test_inventory.json 갱신 (6,801 TC, source_hash 최신화)

---

## 다음 단계

**V622**: SP-B.3 retrofit 3건 (ADR-089)
- SharedCharacterDB v2 ConflictPolicy 5종
- MultiWorkOrchestrator v2 WorkloadProfile + SLO
- RewardModel AdvSeed + score_with_adv_seeds()
