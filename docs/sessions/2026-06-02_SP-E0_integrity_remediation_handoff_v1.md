# SP-E.0 무결성 회복 — 실행 핸드오프 (Phase E 진입 선결, 비협상)
**작성** 2026-06-02 · **측정 HEAD** 2ea1809 · **대상** 저연산 개발 모드 / 집 로컬 실행

Phase E 진입 전 반드시 끝내야 하는 단 하나의 선결과제. 통과 전까지 이후 모든 게이트의 신뢰가 성립하지 않는다.

## 0. 측정 현황 (2026-06-02 실측)
| 항목 | 상태 |
|---|---|
| 내부 SHA256SUMS.txt 대조 | 정상 880 / **해시불일치 54** / 누락 74 (총 971) — **결함 지속** |
| 불일치 원인 | phase-d-exit 막판 패치 + 이후 변경분에 매니페스트 미재생성 |
| test_inventory.json | stale(6801, 2026-05-25). 정상 환경 재생성 필요(본 점검 환경은 deps 부족으로 0 tests 수집 → 사용 금지) |
| ADR 문서 완전성 | **정정**: ADR-037/038 "2파일 분실"이 아님. INDEX는 extract_adr.py 자동생성이며 ADR-001~013·037·038 등 **15개가 "코드 참조 O·문서 X"** 광범위 패턴. **릴리즈 블로커 아님** |
| release_gate 매니페스트 재생성 게이트 | **없음** |
| 보유 도구 | `tools/generate_test_inventory.py`(존재), `tools/phase_e_manifest_validator.py`(존재) — 활용 가능 |

> **이전 평가 정정**: 본 핸드오프 작성자(기획 모드)가 앞서 "ADR-37·38 실누락"이라 한 것은 과장. 실제는 다수 ADR 미문서화(저우선). 진짜 블로커는 **SHA256SUMS 자기검증 불가**다.

## 1. TD-E0-1 (핵심) — SHA256SUMS 재생성 + 게이트
가장 중요. 패키지가 자기 자신을 검증하도록 만든다.

### 1a. 매니페스트 생성 스크립트 신설 — `tools/generate_sha256sums.py`
- **스코프 명문화**(현재 ad-hoc): 어떤 파일 집합을 매니페스트에 넣을지 결정론적으로 정의. 권고 = git 추적 파일 중 릴리즈 대상(코드·데이터; docs/sessions 산출물·.git 제외).
- 출력: `SHA256SUMS.txt` (상대경로 + sha256).
- 멱등: 동일 트리 → 동일 매니페스트.

### 1b. release_gate에 `G_INTEGRITY_MANIFEST` 추가
- 빌드 **마지막 단계**에서 generate_sha256sums.py 재생성 → `sha256sum -c SHA256SUMS.txt` 실행.
- 해시불일치 ≥1건이면 **릴리즈 FAIL** (release_gate.py 게이트 등록).
- 기존 `phase_e_manifest_validator.py`와 연계(중복 로직 통합 검토).

### 1c. Exit 기준
- `sha256sum -c SHA256SUMS.txt` → **해시불일치 0건**.

## 2. TD-E0-2 — test_inventory 재생성 (정상 환경)
- **전제**: 전체 deps 설치 + 테스트 수집이 정상인 환경(집 로컬). 본 점검 환경은 0 tests → 사용 금지.
- 실행: `python tools/generate_test_inventory.py --output tools/test_inventory.json`
- 릴리즈 파이프라인에 hook + `source_hash` 불일치 시 FAIL.
- Exit: test_count 실제값 반영, source_hash 일치.

## 3. TD-E0-3 (정정·하향) — ADR 문서 완전성
- 발견 정정: 2파일 분실 아님 → 15개 미문서 ADR(코드 참조 O). **릴리즈 블로커 아님, 점진 문서화**.
- 권고: ADR-037/038은 소스 참조 위치 확인 후 짧게 문서화. INDEX는 `tools/extract_adr.py`로 자동 재생성(수동 편집 금지 — 덮어써짐).
- Exit(선택): 미문서 ADR 점진 작성, INDEX 재생성.

## 4. SP-E.0 종합 Exit 기준
1. [ ] `sha256sum -c SHA256SUMS.txt` 해시불일치 0건
2. [ ] G_INTEGRITY_MANIFEST 게이트 release_gate 등록 + PASS
3. [ ] test_inventory 정상 환경 재생성 + source_hash 일치
4. [ ] (선택) ADR-037/038 문서화 + INDEX 자동 재생성
→ 1·2·3 충족 시 SP-E.0 완료, Phase E 진입 게이트 통과.

## 5. 실행 순서 (개발 모드)
1. `tools/generate_sha256sums.py` 작성(스코프 결정).
2. release_gate.py에 G_INTEGRITY_MANIFEST 추가(빌드 말미 재생성+검증).
3. 매니페스트·inventory 재생성 → `sha256sum -c` 0 확인.
4. 커밋·태그 재발행(v13.0.x) → 이후 Phase E SP-E.1 진입.

## 6. 비고
- 본 핸드오프는 설계·검증 산출물. 실제 코드(release_gate·generate_sha256sums) 구현은 개발 모드.
- 이 작업은 결정 D1~D26과 무관하게 **즉시 착수 가능**.
