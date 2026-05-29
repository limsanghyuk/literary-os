# CHANGELOG V713

**날짜**: 2026-05-28  
**버전 태그**: v12.2.0-V713 (베이스 12.2.0 유지)  
**SP**: SP-D.3 Plugin Whitelist + Sandbox  
**Gate**: G87 진행 중

---

## 변경 사항

### 신규 모듈

| 모듈 | 클래스/심볼 | 설명 |
|------|-------------|------|
| `literary_system/plugins/plugin_whitelist.py` | `PluginWhitelist`, `DEFAULT_ALLOWED_MODULES`, `BLOCKED_MODULES` | 허용 모듈 화이트리스트 |
| `literary_system/plugins/plugin_sandbox.py` | `PluginSandbox`, `SandboxResult`, `SandboxSecurityError`, `SandboxTimeoutError` | RestrictedPython 코드 실행 격리 |

### 수정 모듈

| 모듈 | 변경 내용 |
|------|-----------|
| `literary_system/plugins/__init__.py` | Whitelist + Sandbox 심볼 추가 익스포트 |

### 신규 테스트

| 파일 | TC 수 | 결과 |
|------|-------|------|
| `tests/unit/test_v713_plugin_sandbox.py` | 33 | ✅ 33 PASS |

**테스트 클래스 구성:**
- `TestPluginWhitelistDefaults` (TC01~08): 기본 허용/차단 목록 검증
- `TestPluginWhitelistMutation` (TC09~16): 동적 변경 및 부모 패키지 매칭
- `TestSandboxBasic` (TC17~24): 기본 실행, 리터럴 연산, import, 결과 캡처
- `TestSandboxSecurity` (TC25~33): os/sys/subprocess/socket 차단, 격리 검증

### 신규 문서

- `docs/adr/ADR-174.md`: PluginWhitelist + PluginSandbox 설계 결정

---

## 보안 사양

| 항목 | 값 |
|------|----|
| 기본 허용 모듈 수 | 30개 (stdlib 안전 부분집합) |
| 항상 차단 모듈 수 | 23개 (os, sys, subprocess 등) |
| 출력 캡처 한도 | 64 KB |
| 실행 격리 | 호출당 독립 네임스페이스 |

---

## 누적 TC 현황

| 구간 | TC |
|------|----|
| V712 누적 | 9,766 |
| V713 신규 | +33 |
| **V713 누적** | **9,799** |

---

## 다음 버전 예고

**V714**: Plugin Lifecycle Management (ADR-175)
- `PluginLifecycleManager`: 플러그인 활성화/비활성화/재시작
- 생명주기 훅: `on_activate`, `on_deactivate`, `on_error`
- 예상 TC: +33
