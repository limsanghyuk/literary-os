# Backend Incident(백엔드 장애) & Recovery Rule(복구 규칙) R1

## Incident(장애)
2026-09-05 세션 말미에 local container/python backend(로컬 컨테이너·파이썬 백엔드)가 최소 명령에서도 반복적으로 `ClientError(클라이언트 오류)`를 반환했다.

재현 범위:
- `container.exec` 최소 명령 실패
- `python.exec` 최소 실행 실패
- `python_user_visible` 최소 파일 생성 실패

따라서 현재 1차 원인은 특정 P07 코드, DB59, R-B 사전등록 또는 ZIP 내용이 아니라 **세션 로컬 CAAS 실행계층 장애**로 분류한다.

## Scientific Boundary(과학적 경계)
이 장애 때문에 실행하지 못한 R-B 결과를 PASS/FAIL로 추정하지 않는다. 현재 R-B 상태는 `LOGIC_PREREGISTERED__EXECUTION_NOT_STARTED`다.

## Preservation Mitigation(보존 우회)
- GitHub `limsanghyuk/literary-os`에 `handoff/p07-preformal-rb-20260905` 브랜치를 생성했다.
- 이 브랜치에 세션의 현재상태, 연구·실험 인계, 8패키지 갱신 매트릭스, R-B 사전등록, 미완료 순서를 보존했다.
- main/Production(메인·운영)은 변경하지 않는다.

## Recovery Procedure(복구 절차)
새 세션에서:
1. container/python 최소 probe(탐침)를 먼저 실행한다.
2. 정상화되면 기존 최신 8 ZIP의 CRC/SHA256을 검사한다.
3. 최신 4개 변경 패키지 CONTROL/A/B2/C2를 추출하고 이 handoff 디렉터리를 append-only(추가 전용)로 편입한다.
4. B1/C1/D1/D2는 바이트 불변으로 유지한다.
5. 새 revision ZIP, SHA256SUMS, CRC, Fresh Validation(새 검증), START HERE(시작문서), Trust Root(신뢰루트)를 만든다.
6. 그 뒤 R-B 실행에 들어간다.

## Do Not(금지)
- 오류가 사라졌다고 이전 실패를 덮어쓰지 않는다.
- ClientError 동안 생성된 불완전 ZIP을 정본으로 승격하지 않는다.
- 기존 ENG:R47 Production 또는 DB59를 수정하지 않는다.