# Changelog — V588 (9.3.0)

**날짜**: 2026-05-21  
**태그**: v9.3.0-V588  
**ADR**: ADR-049  
**Gate**: G47 QueryInterfaceGate (L1)

---

## SP-A.1 — LOSDB QueryInterface + Qdrant 인프라

### 신규

#### `literary_system/db/query_interface.py` (신규, 287 lines)

- `QueryInterface` — LOSDBClient Facade 위 도메인 쿼리 통합 레이어
  - `find_scenes(character, similar_to, graph_within_hops, episode_range, limit)` — 씬 복합 조건 검색
  - `find_characters(similar_personality, limit)` — 성격 벡터 유사도 캐릭터 검색
  - `cross_backend_aggregate(group_by, metric, backends)` — 복수 백엔드 집계 (count / score_sum / score_avg)
  - `health()` — 백엔드 연결 상태 확인
- `SceneResult` dataclass — `(scene_id, episode, label, backend, score, metadata)`
- `CharacterResult` dataclass — `(character_id, name, similarity, backend, metadata)`
- `AggregateResult` dataclass — `(group_key, metric_value, backend_counts, records)`
- SLO 1.0초 (ADR-049 C1): 모든 메서드 elapsed 측정 + 초과 시 WARNING 로그
- LLM-0 원칙: 외부 LLM 호출 0건

#### `tests/unit/test_query_interface.py` (신규, 310 lines)

- TC01~TC05: 초기화 (client/no_client/timeout)
- TC06~TC12: find_scenes (character/vector/graph/dedup/limit/episode_range)
- TC13~TC18: find_characters (similarity/limit/backend_missing)
- TC19~TC24: cross_backend_aggregate (count/score_sum/score_avg/backend_counts)
- TC25~TC30: health + 유틸리티
- **30/30 PASS**

#### `tests/integration/test_qdrant_live.py` (신규)

- Qdrant 미실행 시 자동 SKIP
- 실행 시: 접속 확인 / 컬렉션 생성·삭제 / upsert+search SLO < 1초

#### `docs/adr/ADR-049.md` (신규)

### 수정

| 파일 | 변경 내용 |
|------|---------|
| `literary_system/db/__init__.py` | QueryInterface / SceneResult / CharacterResult / AggregateResult export |
| `literary_system/gates/release_gate.py` | G47 `_gate_query_interface_g47()` 추가 + _GATE_TIER L1 등록 |
| `literary_system/gates/gate_registry.py` | `query_interface_g47` (ADR-049, V588, L1) 등록 |
| `docker-compose.yml` | Qdrant v1.7.4 서비스 추가 (profiles: dev, port 6333/6334) |
| `pyproject.toml` | version 9.2.0 → 9.3.0 |
| `MANIFEST.md` | 버전·게이트 수 갱신 |

---

## Gate 현황

| Gate | ID | ADR | Layer | 버전 |
|------|-----|-----|-------|------|
| G47 | `query_interface_g47` | ADR-049 | L1 | V588 |

**총 46 Gates PASS** (G1~G47)

---

## 수치

| 항목 | V587 (v9.2.0) | V588 (v9.3.0) |
|------|--------------|--------------|
| Gates | 45/45 | **46/46** |
| 신규 테스트 | — | **+30** (TC01~TC30) |
| ADR | ADR-001~048 | **ADR-001~049** |

---

## Gate G47 체크포인트 (8/8 PASS)

| CP | 검증 |
|----|------|
| QI-1 | QueryInterface 임포트 ✅ |
| QI-2 | 데이터클래스 3종 존재 ✅ |
| QI-3 | find_scenes no_client → [] ✅ |
| QI-4 | find_characters no_client → [] ✅ |
| QI-5 | cross_backend_aggregate no_client → [] ✅ |
| QI-6 | health no_client → {"status":"no_client"} ✅ |
| QI-7 | SLO_RESPONSE_SEC == 1.0 ✅ |
| QI-8 | LLM-0: 외부 LLM 호출 0건 ✅ |

---

## 다음: SP-A.2 (V589) — BackendHealthMonitor + HybridSearchV2
