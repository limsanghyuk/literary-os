# CHANGELOG V724

**날짜**: 2026-05-29 | **버전**: v12.3.8 | **단계**: SP-D.3 Chaos Engineering

## 신규

| 파일 | 설명 |
|------|------|
| `literary_system/chaos/__init__.py` | chaos 패키지 (V724 기반) |
| `literary_system/chaos/chaos_engine.py` | ChaosEngine + FaultSpec + FaultType + FaultResult |
| `literary_system/chaos/fault_injector.py` | FaultInjector + InjectionPoint + InjectorRecord |
| `tests/unit/test_v724_chaos_engine.py` | 33 TC PASS |
| `docs/adr/ADR-185.md` | 설계 결정 |

## 주의

chaos/ 패키지 현재 고립 상태(ADR-128 WARN 1버전). V725 G88 Gate에서 반드시 연결.
