# ADR-072: SP-B.3 통합 릴리즈 — MultiWork v2 + LoRA Stacking 완성

**상태**: Accepted  
**날짜**: 2026-05-23  
**버전**: V612 (v10.17.0)  
**작성자**: Literary OS Engineering

---

## 컨텍스트

SP-B.3 (MultiWork v2 + LoRA Stacking)은 V607~V611에 걸쳐 7개 모듈을 점진적으로 구현해 왔다.

| 버전 | 모듈 | ADR |
|------|------|-----|
| V607 | SharedCharacterDBV2, SharedWorldDBV2 | ADR-067 |
| V608 | MultiWorkOrchestratorV2 | ADR-068 |
| V609 | MultiWorkCIMV2 | ADR-069 |
| V610 | MultiWorkCIM v2.0 업그레이드 | — |
| V611 | GenreTransferV2, GenreAdaptationReport | ADR-071 |
| V612 | LoRAStackingAdapter (serving층) | 본 ADR |

V611까지 6개 모듈이 완성됐으나 **릴리즈 게이트가 없어** 품질 보증 계층이 부재했다.  
V612는 Gate G58·G59를 신설해 SP-B.3를 완전히 닫는다.

---

## 결정

### 1. LoRAStackingAdapter (literary_system/serving/lora_stacking_adapter.py)

SP-B.3의 최종 실행 계층. 복수 LoRA 가중치를 선형 결합해 단일 모델 패치를 생성.

```
GenreTransferV2.weighted_transfer()
       ↓  GenreAdaptationReport (source_genre, target_genre)
LoRAStackingAdapter.genre_stack([genres], project_id)
       ↓  StackResult (merged_weights, coefficients, coeff_sum)
LoRAStackingAdapter.apply_to_model(stack_result, model_id)
       ↓  Dict[str, Any] → LLM 서빙 레이어 주입
```

핵심 계약:
- `stack(weight_ids, coefficients)`: `sum(coefficients) != 1.0` → `ValueError`
- `genre_stack(genres, project_id)`: 동일 계수 자동 정규화, `coeff_sum == 1.0`
- `normalize_coefficients(weight_ids, raw_coeffs)`: 합 → 1.0 재조정
- `VERSION = "1.0.0"` 불변

### 2. Gate G58 — LoRAStackingAdapter 검증 (8 CPs)

```python
GATES.append(("lora_stacking_g58", "...", _gate_lora_stacking_g58))
```

| CP | 검증 내용 |
|----|-----------|
| CP-1 | import + VERSION=="1.0.0" |
| CP-2 | register / get / list_by_genre |
| CP-3 | stack() 선형 결합 정확도 (0.6×0.5 + 0.4×0.2 = 0.38) |
| CP-4 | coeff_sum ≠ 1.0 → ValueError |
| CP-5 | genre_stack() 자동 정규화 |
| CP-6 | normalize_coefficients() 합 재조정 |
| CP-7 | apply_to_model() 구조 키 확인 |
| CP-8 | stats() 키 완전성 |

### 3. Gate G59 — SP-B.3 Exit Gate (7 CPs)

```python
GATES.append(("sp_b3_exit_g59", "...", _gate_sp_b3_exit_g59))
```

| CP | 검증 대상 |
|----|-----------|
| CP-1 | SharedCharacterDBV2 (add_character / get_character) |
| CP-2 | SharedWorldDBV2 (add_location / get_location) |
| CP-3 | MultiWorkOrchestratorV2 |
| CP-4 | MultiWorkCIMV2 (version enum + reward_weighted_global_weight) |
| CP-5 | GenreTransferV2 + GenreAdaptationReport + weighted_transfer |
| CP-6 | LoRAStackingAdapter (genre_stack) |
| CP-7 | 데이터 흐름: weighted_transfer → genre_stack → coeff_sum==1.0 |

### 4. 모듈 생명주기 처분 원칙 (PREFLIGHT_GUIDE_v2.0 §6)

V612 Preflight 단계에서 확립한 5단계 처분 프로토콜:

1. **승격(Promotion)**: 레거시 → 신 아키텍처 격상
2. **보완(Supplement)**: 신 로직이 구 로직을 호출·확장
3. **보강(Reinforce)**: 신 로직이 구 로직을 강화
4. **대체(Replace)**: 신이 구를 완전 흡수 (ADR 문서화 필수)
5. **폐기(Deprecate)**: 1~4 불가 시에만 허용

ORPHAN_DISPOSITION dict를 preflight_step15.py에 등록해 자동 추적.

---

## 결과

- **Gates**: 56 → **58** (G58 + G59 신설)
- **테스트**: 6500 → **6527** (+27 TC)
- **버전**: v10.16.0 → **v10.17.0**
- SP-B.3 공식 완료 — 7모듈 + 2 Gate + ADR-067~072

---

## 트레이드오프

| 항목 | 선택 | 이유 |
|------|------|------|
| genre_stack project_id 필수 | 필수 인자 | 프로젝트 격리·히스토리 추적 |
| CIMVersion enum (클래스 속성) | 불변 속성 | 런타임 변경 방지 |
| weighted_transfer → genre_stack 연계 | 느슨한 결합 | genre 이름 기반 조인, 강한 의존 없음 |

---

## 관련 ADR

ADR-067 (SharedDB v2) · ADR-068 (OrchestratorV2) · ADR-069 (CIMV2) · ADR-071 (GenreTransfer)
