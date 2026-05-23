# Changelog — V595 (v10.0.0) Phase A Complete

**릴리즈일**: 2026-05-21  
**이전 버전**: V594 v9.9.0 → **현재**: V595 v10.0.0  
**커밋**: (pending)  

---

## 🎉 Phase A 완료 마일스톤

Literary OS Phase A (V581~V595, 8 서브페이즈) 전체 완료.

---

## 신규 구현 (SP-A.8)

### Minimal-CLI v0.1 (`apps/cli/literary_cli.py`)
- `literary analyze <scene_file>` — 5축 LOSConstitution 품질 분석 (text/json 출력)
- `literary repair <series_id>` — 시리즈 품질 진단 + 수리 제안 (LLM-0)
- `literary generate -e N -s M` — 장면 생성 (CorpusFallbackPipeline + Constitution 검증)

### Phase A Exit Gate G52 (`literary_system/gates/phase_a_exit_gate.py`)
- EA-1: CLI 3 commands 존재 확인
- EA-2: score_scene_full() 5축 분해 기능
- EA-3: CorpusFallbackPipeline.collect() 기능
- EA-4: R(scene) >= 0.60 (_RICH_SCENE*3 기준)
- EA-5: GATES >= 51 + G51 PASS
- EA-6: pytest --collect-only >= 6,000

### ADR-055 (`docs/adr/ADR-055.md`)
- Phase A Exit Gate 설계 결정 기록
- Phase B 진입 조건 명시 (V596~)

---

## 수치

| 항목 | V594 (9.9.0) | V595 (10.0.0) |
|---|---|---|
| Gates | 50/50 | **51/51** (+G52) |
| 신규 테스트 | — | **+40** (TC01~TC20 ×2) |
| 총 테스트 수집 | 6,139 | **6,179** |
| ADR | 001~054 | **001~055** |
| Minimal-CLI | 없음 | **v0.1 (3 commands)** |
| Phase A | 진행 중 | **완료** |

---

## Phase B 예고 (V596~)

- Phase B.1: Fine-tuning Pipeline (LoRA 실 학습)
- Phase B.2: RLHF Loop (헌법 기반 보상 신호)
- Phase B.3: Multi-work 협업 프레임워크
- 목표: v11.0.0 / 60 Gates / 7,000 PASS
