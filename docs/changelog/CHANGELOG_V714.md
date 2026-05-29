# CHANGELOG — V714

**버전**: V714  
**날짜**: 2026-05-28  
**단계**: SP-D.3 Plugin Registry (G87)

---

## 요약

PluginLifecycleManager 상태 기계 구현. 활성화·비활성화·재시작 전환과 훅 시스템으로
플러그인 생명주기를 정형화한다.

---

## 신규 모듈

| 모듈 | 설명 |
|------|------|
| `literary_system/plugins/plugin_lifecycle.py` | LifecycleState / LifecycleRecord / PluginLifecycleManager |

---

## 신규 심볼

| 심볼 | 위치 | 설명 |
|------|------|------|
| `LifecycleState` | plugin_lifecycle | 6-상태 열거체 (INACTIVE/ACTIVATING/ACTIVE/DEACTIVATING/INACTIVE_ERROR/RESTARTING) |
| `LifecycleRecord` | plugin_lifecycle | 플러그인별 상태·오류·활성화 횟수 레코드 |
| `PluginLifecycleManager` | plugin_lifecycle | 상태 기계 + 훅 시스템 메인 클래스 |

---

## 버그 수정

| 버그 | 설명 | 수정 |
|------|------|------|
| restart() 훅 미실행 | RESTARTING 상태 선행 설정으로 deactivate() 가드 우회 | deactivate() 먼저 실행 후 RESTARTING 전환 |

---

## 신규 ADR

- **ADR-175**: PluginLifecycleManager 설계 결정

---

## 테스트

| 파일 | TC 수 | 결과 |
|------|-------|------|
| `tests/unit/test_v714_plugin_lifecycle.py` | 33 | ✅ 33/33 PASS |

누적 테스트 수: **9,832** (V713 9,799 + 33)

---

## 변경 파일

```
literary_system/plugins/plugin_lifecycle.py     [신규]
literary_system/plugins/__init__.py             [업데이트: 3심볼 추가]
tests/unit/test_v714_plugin_lifecycle.py        [신규]
docs/adr/ADR-175.md                             [신규]
docs/changelog/CHANGELOG_V714.md               [신규]
```
