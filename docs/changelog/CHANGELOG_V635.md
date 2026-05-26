# CHANGELOG V635 — v11.5.0

## 릴리즈 정보
- **버전**: v11.5.0
- **Phase**: C SP-C.1 (Self-Learning Loop)
- **테마**: AutoPromotionGate G62 — LoRA 자동 승격 게이트 (ADR-077)
- **날짜**: 2026-05-26

## 핵심 변경

### 신규 파일
| 파일 | 설명 |
|------|------|
| `literary_system/gates/auto_promotion_gate.py` | AutoPromotionGate + GateResult + run_g62_gate() (364줄) |
| `tests/unit/test_v635_auto_promotion_gate.py` | TC-01~33, 33/33 PASS |
| `docs/adr/ADR-077.md` | 자동 승격 게이트 설계 결정 |
| `docs/changelog/CHANGELOG_V635.md` | 본 파일 |
| `manifests/MANIFEST_V635.md` | V635 산출물 매니페스트 |

### 수정 파일
| 파일 | 변경 내용 |
|------|----------|
| `literary_system/constitution/__init__.py` | AutoPromotionGate, GateResult, R_THRESHOLD, MAX_ROLLBACKS 공개 |
| `literary_system/gates/release_gate.py` | G62 체크포인트 추가 → 60→61 Gates |
| `pyproject.toml` | 11.4.0 → 11.5.0 |
| `tools/test_inventory.json` | 7,346 → 7,379 TC |

## 테스트 현황
- **전체 TC**: 7,379 (단위 1,182 PASS)
- **신규 TC**: 33 (TC-01~33)
- **Gates**: 61/61 PASS (G62 신규 추가)

## Gate G62
- CP-1~CP-7 모두 PASS
- 골든셋 10개 장면 평균 R=0.814 ≥ 0.78
- 롤백 0건 확인

## LLM-0 준수
외부 LLM 호출 없음. DEV_MODE=false.
