# CHANGELOG V594 — SP-A.7 LOSConstitution v1.0 (v9.9.0)

## 릴리즈 정보
- **버전**: 9.9.0 (V594)
- **릴리즈일**: 2026-05-21
- **태그**: v9.9.0
- **Gate**: G51 ConstitutionGate (CT-1~CT-10, 10/10 PASS)
- **기반**: v9.8.0 (V593 CorpusValidator)

---

## 변경 사항

### 신규 패키지: `literary_system/constitution/`

#### `los_constitution.py` (신규, ~260 lines)
- `ConstitutionWeights` (frozen dataclass) — 5축 가중치 (합계=1.0 검증)
  - drse=0.30 / debt=0.20 / arc=0.20 / tension=0.15 / prose=0.15
- `ConstitutionSceneScore` — 5축 분해 + R(scene) 가중합
- `ConstitutionWorkScore` — 작품 집계 (mean/variance/work_score)
- `LOSConstitution` — 핵심 클래스
  - `score_scene(scene) → float` (R(scene))
  - `score_scene_full(scene) → ConstitutionSceneScore`
  - `score_work(scenes) → ConstitutionWorkScore`
  - `rlhf_reward(generated, original) → float`
- 5축 텍스트 메트릭 함수 (LLM-0):
  - `_score_drse` — length + TTR + narrative marker
  - `_score_debt` — 미결 플롯훅 대비 해소율
  - `_score_arc` — 기승전결 4막 구조 신호
  - `_score_tension` — 갈등/긴장 마커 밀도
  - `_score_prose` — TTR + 문장 길이 변화
- W(work) = mean(R_i) − 0.10·var(R_i)
- R_rlhf = clamp(R(generated) − R(original), −1.0, 1.0)

### Gate + ADR

- **Gate G51** (`release_gate.py`, CT-1~CT-10, 10/10 PASS)
- **gate_registry.py**: `constitution_g51 → ADR-054, V594, L1`
- **ADR-054** (`docs/adr/ADR-054.md`) — LOSConstitution v1.0

### 테스트

- `tests/unit/test_los_constitution.py` (TC01~TC40, 40/40 PASS)
  - TC01~TC06: ConstitutionWeights (기본값, 합계, 수정 불가)
  - TC07~TC12: 5축 개별 함수 검증
  - TC13~TC20: score_scene() str/dict 입력, 가중합 정확성
  - TC21~TC28: score_work() mean/variance/공식 검증
  - TC29~TC33: rlhf_reward() 범위/방향성
  - TC34~TC40: 50개 장면 통합, LLM-0

---

## 수치

| 항목 | V593 (9.8.0) | V594 (9.9.0) |
|---|---|---|
| Gates | 49/49 | **50/50** (+G51) |
| 신규 테스트 | — | **+40** |
| ADR | ADR-001~053 | **ADR-001~054** |
| LOSConstitution | 없음 | **v1.0 구현 완료** |
| R(scene) 평균 | — | **≥ 0.65** |
| variance | — | **≤ 0.05** |

---

## 보안/아키텍처 제약 (계속 유효)

- **LLM-0 원칙**: 외부 LLM 호출 0건
- **DEV_MODE** 기본값 항상 `"false"` (ADR-034)
