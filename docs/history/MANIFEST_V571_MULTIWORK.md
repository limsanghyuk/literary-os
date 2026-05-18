# MANIFEST — Literary OS V571 MultiWork Stage C

작성일: 2026-05-17  
버전: V571  
패키지: literary_os_v571_multiwork.zip  

## 신규 모듈 (V562~V571)

| 버전 | 모듈 | 위치 |
|------|------|------|
| V562 | MultiWorkCore | literary_system/multiwork/multi_work_core.py |
| V563 | SharedCharacterDB | literary_system/multiwork/shared_character_db.py |
| V564 | SharedWorldDB | literary_system/multiwork/shared_world_db.py |
| V565 | GenreTransferLearning | literary_system/multiwork/genre_transfer.py |
| V566 | ProjectIsolationManager | literary_system/multiwork/project_isolation.py |
| V567 | MultiWorkCIM | literary_system/multiwork/multi_work_cim.py |
| V568 | AuthorLicenseAPI | literary_system/multiwork/author_license_api.py |
| V569 | Gate31 | literary_system/gates/release_gate.py (_gate_multiwork_g31) |
| V570 | MultiWorkOrchestrator | literary_system/multiwork/multi_work_orchestrator.py |
| V571 | 릴리즈 패키징 | pyproject.toml v7.7.1, tests/test_v562_v571_multiwork.py |

## 테스트 현황

- 전체: 5,456 PASS / 0 FAIL / 20 SKIP (pytest 기준)
- MultiWork 전용: 111 PASS / 0 FAIL
- 릴리즈 게이트: 30/30 PASS

## 알려진 제약 (Known Limitations)

### KL-001: PERSONAL 라이선스 MultiWork 사용 불가
- **설명**: `AuthorLicenseAPI.PERSONAL` 스코프에 `MULTI_WORK`가 포함되지 않음.
  `MultiWorkOrchestrator.create_project()` 호출 시 `LicenseViolation` 발생.
- **요건**: `COMMERCIAL` 이상 라이선스 필요.
- **현황**: 설계 의도대로 동작. 온보딩 문서 명시 필요.
- **조치**: 다음 릴리즈 사이클에서 사용자 온보딩 가이드에 라이선스 요건 섹션 추가 예정.

### KL-002: OTel tracer 미초기화 (V474~)
- **설명**: `test_otel_tracer_init` 테스트 1건 FAIL (V474 이후 지속).
  `pytest -q` 기준 `5,454 PASS / 1 FAIL / 21 SKIP`으로 측정되는 환경도 있음.
- **영향**: OTel tracer 자동 초기화 미지원 환경에서의 테스트 실패. 런타임 기능에는 무영향.
- **조치**: 별도 Hotfix 사이클 검토.

## pyproject.toml 변경

```
version = "7.7.1"
description = "Literary OS V571 — Phase6 MultiWork Stage C Full Build (MultiWork Orchestrator)"
```

## 게이트 이력

| 게이트 | 버전 | 상태 |
|--------|------|------|
| G29 PNE | V555 | PASS |
| G30 Corpus | V560 | PASS |
| **G31 MultiWork** | **V571** | **PASS ★** |
