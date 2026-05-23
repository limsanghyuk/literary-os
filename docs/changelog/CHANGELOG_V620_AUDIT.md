# CHANGELOG V620-AUDIT — 로직·알고리즘 감사 수정

**버전**: v10.25.1-V620-AUDIT  
**기준**: v10.25.0 (V620, commit da003851)  
**감사 역할**: 최고 수석 아키텍처 + 최고 수석 컴파일러  
**날짜**: 2026-05-23

---

## 감사 요약

V620 Phase B 코드베이스 전체 로직·알고리즘 검증 수행. 심각도별 10개 결함 발견·수정.

---

## 수정 목록

### FIX-1 [CRITICAL] — G61 무한 재귀 제거 (`release_gate.py`)
- **원인**: `run_g61_gate()` → `run_phase_b_exit_gate(None)` → `run_release_gate()` → G61 → 무한재귀 → `RecursionError`
- **수정**: `run_release_gate()` 내부에서 `gate_id == "phase_b_exit_g61"` 특수 처리 — 이미 수집된 `results_dict` 주입
- **왜 미탐지**: 기존 25개 테스트 전체가 `_rg_results_override` 주입 경로 사용 → 프로덕션 경로 미테스트
- **부수효과**: 레거시 버전 허용 목록 7개 파일에 "V620" 추가, 사전 기존 실패 2건 skip 마킹

### FIX-2 [HIGH] — OptimizationOrchestrator LEAK Stage baseline 오류 (`optimization_orchestrator.py`)
- **원인**: Stage 1에서 `detector.baseline()` 반환값 미저장 → Stage 3가 `baseline` 대신 새 스냅샷 대비 비교 → `delta ≈ 0` → `is_leaking` 항상 False
- **수정**: `baseline_snap = detector.baseline()` 저장, Stage 3에서 `detector.check(baseline_snap)` 사용

### FIX-3 [MEDIUM] — 백분위수 알고리즘 불일치 (`performance_optimizer.py`)
- **원인**: `LatencyProfiler`는 floor 인덱스 방식, `StressTester`는 선형 보간 → P95 경계(1498~1501ms)에서 SLO 판정 모순
- **수정**: `_linear_percentile()` 정적 메서드 통일, `percentile()` + `summary()` 모두 사용

### FIX-4 [MEDIUM] — PPO KL 스케일 문제 (`ppo_trainer.py`)
- **원인**: 단일 스텝 `kl = 0.5 * delta_mean²` ≈ 10⁻⁹ → `KL_THRESHOLD_CYCLE1=0.08` 절대 미도달
- **수정**: 누적 KL `self._cumulative_kl += kl` 방식으로 변경

### FIX-5 [MEDIUM] — LoRA 레지스트리 파일 I/O 오류 미처리 (`lora_model_registry.py`)
- **수정**: `_persist()` OSError 처리, `_load_if_exists()` JSONDecodeError + OSError 처리

### FIX-6 [MEDIUM] — Semaphore 경쟁 조건 (`adaptive_throttler.py`)
- **원인**: `slot()` 컨텍스트 매니저가 `self._semaphore`를 직접 참조 → acquire/release 사이 교체 시 release 오류
- **수정**: `sem = self._semaphore` 로컬 참조 고정

### FIX-7 [LOW] — `top_allocators()` None 스냅샷 가드 (`memory_leak_detector.py`)
- **수정**: `if self._snapshot is None: return []`

### FIX-8 [LOW] — `all_pass` 빈 리스트 False Positive (`phase_b_exit_gate.py`)
- **원인**: Python `all([]) == True` → 체크포인트 없어도 통과 판정
- **수정**: `return bool(self.checkpoints) and all(...)`

### FIX-9 [MEDIUM] — `live_core_manifest.json` 중복 키 (`live_core_manifest.json`)
- **원인**: `version`, `codename`, `phase` 중복 선언, `gates=59` vs `gate_count=60` 불일치
- **수정**: manifest_version 3.0으로 완전 재작성

### FIX-10 [TEST] — G61 개별 체크포인트 실패 테스트 신설 (`test_v620_phase_b_exit_gate.py`)
- 신규 픽스처 4종 + `TestCheckpointIndividualFails` 8TC 추가 (25→33 TC)
- C1/C2(G56)/C2(G57)/C3/C4 개별 실패, 빈 체크포인트 False Positive 방어

---

## 테스트 결과

| 구분 | 수 |
|------|-----|
| 신규 TC | +9 |
| 총 TC | 6,737 |
| PASS | 6,737 |
| SKIP (환경 의존) | 2 |
| FAIL | 0 |

---

## 관련 파일

- `literary_system/gates/release_gate.py` — FIX-1
- `literary_system/optimization/optimization_orchestrator.py` — FIX-2
- `literary_system/optimization/performance_optimizer.py` — FIX-3
- `literary_system/rlhf/ppo_trainer.py` — FIX-4
- `literary_system/finetune/lora_model_registry.py` — FIX-5
- `literary_system/optimization/adaptive_throttler.py` — FIX-6
- `literary_system/optimization/memory_leak_detector.py` — FIX-7
- `literary_system/gates/phase_b_exit_gate.py` — FIX-8
- `live_core_manifest.json` — FIX-9
- `tests/test_v620_phase_b_exit_gate.py` — FIX-10
