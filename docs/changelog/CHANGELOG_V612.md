# CHANGELOG — V612 (v10.17.0)

**릴리즈 날짜**: 2026-05-23  
**기준**: V611 (v10.16.0, commit 2e5e3715)

---

## 주요 변경 사항

### SP-B.3 통합 완성 (ADR-072)

#### 신규 Gate

| Gate ID | 이름 | CPs |
|---------|------|-----|
| `lora_stacking_g58` | LoRAStackingAdapter Multi-LoRA Stacking Gate | 8 |
| `sp_b3_exit_g59` | SP-B.3 Exit Gate — 7모듈 통합 완성 | 7 |

- **총 Gate**: 56 → 58 (+2)

#### 신규 테스트

- `tests/test_v612_sp_b3_integration.py` — 27 TC
  - TC-1: LoRAStackingAdapter 핵심 인터페이스 (8 TC)
  - TC-2: Gate G58 직접 실행 (3 TC)
  - TC-3: SP-B.3 7모듈 임포트 + 인터페이스 (7 TC)
  - TC-4: CP-7 데이터 흐름 — GenreTransferV2 → LoRAStackingAdapter (2 TC)
  - TC-5: Gate G59 직접 실행 (3 TC)
  - TC-6: 릴리즈 게이트 등록 확인 (3 TC / 비교 포함)

- **총 테스트**: 6500 → 6527 (+27)

### Preflight Step15 v2.0 (V612-P1/P2)

- Rules 1-3 (hygiene) + Rules 4-8 (connectivity) 8-Rule 종합 CI 게이트
- `ORPHAN_DISPOSITION` dict — 16개 레거시 모듈 처분 방향 명시
- `PREFLIGHT_GUIDE_v1.1.md` → `PREFLIGHT_GUIDE_v2.0.md`
  - §6 모듈 생명주기 처분 원칙 (승격→보완→보강→대체→폐기)

### 문서

- `docs/adr/ADR-072-sp-b3-integration-release.md` 작성

---

## 버전

- pyproject.toml: `10.16.0` → `10.17.0`

---

## SP-B.3 완료 요약

| 버전 | 모듈 | 상태 |
|------|------|------|
| V607 | SharedCharacterDBV2, SharedWorldDBV2 | ✅ |
| V608 | MultiWorkOrchestratorV2 | ✅ |
| V609 | MultiWorkCIMV2 | ✅ |
| V610 | MultiWorkCIM v2.0 업그레이드 | ✅ |
| V611 | GenreTransferV2 | ✅ |
| V612 | LoRAStackingAdapter + Gate G58 + Gate G59 | ✅ |

**SP-B.3 COMPLETE** — 7모듈 · 2 Gate · ADR-067~072
