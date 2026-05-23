# Changelog — V618 (v10.23.0)

**Date**: 2026-05-23  
**Version**: v10.23.0  
**SP**: SP-B.4 통합 최적화 + Exit  

---

## 신규 모듈

### `literary_system/optimization/adaptive_throttler.py` (392줄)
- **ThrottleConfig** — 동적 조절 설정 dataclass (임계값, 상·하한, 윈도우 크기)
- **ThrottleEvent** — 단일 조정 이벤트 (action, previous/current, p95, memory)
- **ThrottleReport** — 전체 보고서 (total_calls, avg_latency, reduce/increase 횟수)
- **AdaptiveThrottler** — 메인 조절기 (slot() ctx mgr, record(), reset(), quick_throttle())

## 테스트

- `tests/test_v618_adaptive_throttler.py` — 25 TC, ALL PASS
  - TestThrottleConfig (4) / TestThrottleEvent (4) / TestThrottleReport (4)
  - TestAdaptiveThrottlerCore (8) / TestAdaptiveThrottlerEdgeCases (5)

## ADR

- ADR-078: AdaptiveThrottler v1.0 — SLO 기반 동적 처리량 조절기

## 수치

| 항목 | 이전 (V617) | 이후 (V618) |
|------|------------|------------|
| 버전 | v10.22.0 | v10.23.0 |
| 테스트 | 6,653 PASS | 6,678 PASS |
| Gates | 59/59 | 59/59 |
| ADR | ADR-077 | ADR-078 |

## SP-B.4 진행률

V614 ✅ → V615 ✅ → V616 ✅ → V617 ✅ → **V618 ✅** → V619~V630 (다음)
