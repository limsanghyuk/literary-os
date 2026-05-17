# ADR-014 — Scene Necessity Policy

**날짜:** 2026-05-16  
**상태:** Accepted  
**구현 버전:** V395 (SceneNecessityChecker), V482 (TreeNode 통합)  
**담당 레이어:** `literary_system.longform.scene_necessity`

---

## 맥락 (Context)

드라마 대본에서 "불필요한 씬"은 서사 에너지를 소비하면서 스토리를 전진시키지 않는다. 긴 형식(16화×60분) 시리즈에서는 이 문제가 특히 심각하다 — 씬 수가 많아질수록 약한 씬이 누적되어 시청자 이탈이 발생한다.

기존 접근(인간 편집자 검토)은 확장성이 없다. Literary OS는 **결정론적 수치 기반 필요성 판정**을 통해 LLM 호출 없이 씬 품질을 보장해야 한다.

---

## 결정 (Decision)

### 1. 씬 필요성 판단 기준

씬은 다음 중 하나를 만족할 때 **필요(necessary)**로 판정된다:

| 조건 | 설명 |
|------|------|
| `changed_dimensions ≥ 2` | 8개 상태 차원 중 2개 이상이 THRESHOLD(0.05) 이상 변화 |
| `scene_function_type ≠ NARRATIVE` | ATMOSPHERE 또는 EMOTIONAL_RESIDUE 씬 |

### 2. 상태 차원 8개 (StateDelta)

`belief`, `emotion`, `relationship`, `reveal`, `conflict`, `motif`, `agency`, `curiosity`

각 차원의 변화량이 `|Δ| ≥ 0.05` 이면 "변화 있음"으로 간주.

### 3. 액션 분류

| changed_dims | function_type | 판정 | 권장 액션 |
|---|---|---|---|
| ≥ 2 | any | necessary | `keep` |
| 1 | NARRATIVE | weak | `revise` |
| 0 | NARRATIVE | removable | `merge_or_remove` |
| any | ATMOSPHERE/EMOTIONAL_RESIDUE | necessary | `keep` |

### 4. 게이트 통과 기준

- `weak_scene_ratio < 0.15` — 서사 씬 중 weak 비율 15% 미만
- 3회 이상 연속 `merge_or_remove` → 반복 패턴 경고

### 5. TreeNode 통합 (V482)

`SceneNecessityResult`를 `TreeNode.metadata`에 포함시켜 FractalPlotTree에서 씬별 필요성을 추적한다.

---

## 결과 (Consequences)

**긍정적:**
- LLM 호출 없이 씬 품질 보장 (LLM-0 준수)
- 편집자 작업량 감소: weak 씬 사전 필터링
- 반복 패턴 조기 감지

**부정적/위험:**
- 한국 드라마의 "정서적 여백" 씬이 `ATMOSPHERE`로 올바르게 분류되지 않으면 과도하게 제거될 위험
- 해결: SceneNecessityChecker 사용자는 `scene_functions` 딕셔너리를 통해 ATMOSPHERE/EMOTIONAL_RESIDUE를 명시해야 함

---

## 대안 (Alternatives Considered)

| 대안 | 기각 이유 |
|------|---------|
| LLM 기반 씬 평가 | LLM-0 원칙 위반, 비용 과다 |
| 단순 씬 길이 기준 | 길이와 필요성은 무관 |
| 인간 편집자 전수 검토 | 확장성 없음 |

---

## 구현 참조

- `literary_system.longform.scene_necessity.SceneNecessityChecker`
- `literary_system.longform.scene_necessity.StateDelta`
- `literary_system.schemas.tree_node.TreeNode`
- `tests/test_v482_episode_structure.py`
