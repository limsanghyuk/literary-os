# CHANGELOG V611 — GenreTransferV2 + LoRAStackingAdapter (SP-B.3)

**버전**: v10.16.0  
**날짜**: 2026-05-23  
**커밋**: V611: GenreTransferV2 + LoRAStackingAdapter (ADR-071, SP-B.3)

---

## 신규 모듈

### `literary_system/multiwork/genre_transfer.py` — V611 확장

`GenreTransferV2` 클래스 추가 (기존 `GenreTransferLearning` 상속):

- `weighted_transfer()`: CIM v2 보상 가중치 반영 장르 전이
  - `adjust_alpha = clamp(alpha + boost * CIM.reward_weighted_global_weight, 0, 1)`
  - 캐릭터 보상 평균 → `emotional_intensity` 최대 +0.05 보정
  - 세계관 일관성 < 0.7 → `description_density` 최대 +0.08 보정
- `project_genre_coherence()`: 프로젝트별 장르 전이 일관성 점수 (0~1)
- `recommend_genre()`: CIM 보상 기반 장르 추천 (안전/도전적 전이)
- `adaptation_reports()`: 프로젝트 필터 지원 보고서 이력 조회
- `stats_v2()`: v2 통합 통계

`GenreAdaptationReport` 데이터클래스 추가.

### `literary_system/serving/lora_stacking_adapter.py` — 신규

`LoRAStackingAdapter` + `LoRAWeight` + `StackResult`:

- `register()`: LoRA 가중치 등록 (overwrite 옵션)
- `stack()`: 수동 계수로 복수 LoRA 선형 합산 (Σ coeff = 1.0 검증)
- `genre_stack()`: 장르 목록 + CIM v2 보상 기반 자동 계수 스태킹
- `normalize_coefficients()`: 계수 정규화 유틸리티
- `apply_to_model()`: 모델 적용 스텁 (LLM-0)
- `stats()`: 버전·등록 수·이력 카운트

---

## ADR

- **ADR-071**: GenreTransferV2 + LoRAStackingAdapter 설계 결정

---

## 테스트

- `tests/unit/test_v611_genre_transfer_v2.py`: 12 TC (TC01~TC12)
  - TC01~TC06: GenreTransferV2 핵심 기능
  - TC07~TC10: LoRAStackingAdapter 핵심 기능
  - TC11~TC12: 통합 (CIM v2 + 장르 전이 + LoRA 스태킹)

**총 테스트**: 6,500 (이전 6,488 + 12 TC)

---

## 버전 정보

- `pyproject.toml`: 10.15.0 → 10.16.0
- ADR: ADR-001 ~ ADR-071
- Gate: G01 ~ G57 (56 Gates, 변경 없음)
