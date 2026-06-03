# Literary OS — 문서 지도 (Documentation Map)
> 신규 진입자(개발자·협업자·AI 에이전트)가 저장소 전체를 빠르게 파악하기 위한 최상위 안내. 갱신 2026-06-02.

## 1. Literary OS란
장편 소설·드라마 시나리오 생성을 위한 AI 파이프라인. 현재 정립된 아키텍처 관점은 **"장편 앙상블 서사를 위한 도메인 특화 에이전트 오케스트레이션 프레임워크"**다. 즉 코딩 에이전트가 코드를 짜듯, 거시·미시 플롯과 다인물 앙상블을 미리 분해·설계하는 "씨앗"을 던지고, 생성은 LLM에 위임하되 메모리(NKG)·검증(공식/Critic)·도메인 분해를 불변 핵심으로 유지한다. 공식은 폐기 대상이 아니라 영속 검증층("타입 시스템")이며, LLM 포용은 LLM-0→2.5로 점진 진행한다.
→ 상세: `docs/sessions/2026-06-02_agentic_orchestration_consensus_v1.docx` (3인 합의)

## 2. 저장소 지도 (코드·문서·실험)
| 위치 | 내용 |
|---|---|
| `literary_system/` | 핵심 엔진 코드 (NKG·공식·Critic·게이트·finetune 등 87 모듈군) |
| `apps/` | 응용 (studio_api 등) |
| `experiments/` | 검증 실험 — `value_proof/`(구조 vs 순수 LLM MVE 하니스) |
| `tools/` | preflight·release gate·유틸 (29개) |
| `tests/` | 테스트 (240 디렉토리/모듈) |
| `manifests/` | 버전 매니페스트 |
| `docs/` | 모든 문서 (아래 §3) |
| 루트 README.md | 빠른 시작·시스템 개요 (⚠️ §6 참고: 버전 stale) |
| CLAUDE.md / AGENTS.md / SESSION_INIT.md | AI 에이전트용 작업 규약 |

## 3. docs/ 안내 (하위 11종)
| 폴더 | 내용 | 진입점 |
|---|---|---|
| `sessions/` (84) | 세션별 기획·제안서·설계도·핸드오프·실험 결과 모음 | **`sessions/INDEX.md`** ← 전체 카탈로그+정본표 |
| `proposals/` (10) | 제안서 모음 | `proposals/INDEX.md` |
| `phase/` (2) | Phase별 설계 docx (B·C) | — |
| `adr/` (193) | 아키텍처 결정 기록 (ADR-014~208) | `adr/INDEX.md` |
| `designs/` (4) | 설계 노트 (V583~) | — |
| `workflow/` (6) | 개발 규약·브랜치 전략 (DEV_PROTOCOL_v3.0) | `workflow/DEV_PROTOCOL_v3.0.md` |
| `user/` (4) | 사용자 가이드 | `user/quickstart.md` |
| `sdk/` (4) | API 예제 (postman·curl·node) | `sdk/` |
| `changelog/` (130) | 버전별 변경 이력 | — |
| `history/` (17) | 무결성 증명·구 매니페스트 | — |
| `perf/` (1) | 게이트 타이밍 | — |

## 4. 어디부터 읽나 (역할별 온보딩 경로)
- **처음 오는 사람**: 루트 README → 본 지도 → `sessions/INDEX.md §1 정본표`.
- **현재 방향이 궁금**: `sessions/2026-06-02_agentic_orchestration_consensus_v1.docx` + `2026-06-02_phase_efg_planning_report_v1.docx`.
- **이어서 작업**: `sessions/2026-06-02_home_continuation_playbook.md`.
- **AI 에이전트**: `CLAUDE.md` → `AGENTS.md` → `SESSION_INIT.md` → `workflow/DEV_PROTOCOL_v3.0.md`.

## 5. 현재 상태 (2026-06-02)
**모델의 여러 문제를 해결하기 위한 논의 단계.** 핵심 미해결 명제 = "구조(에이전트 오케스트레이션)가 강한 LLM 베이스라인보다 일관된 앙상블 서사를 만드는가"(G_VALUE_PROOF). 진입 방식 = 검증 우선 입구 관문(SP-E.0 무결성 → 사전실험 → 최소슬라이스 검증 → go/no-go). 정리·검증이 끝나면 본격 Phase E 설계로 이행.

## 6. 알려진 보완 사항 (정직한 기록)
1. **루트 README.md가 stale**: `V730 / v12.4.0 / 9766 tests / 88 gates` 표기 = 현재 V745 / v13.0.0와 불일치. 권위 있는 수치로 갱신 필요(개발 모드).
2. **docs/sessions 정리 잔여**: 빌드 산출물(.js) 분리·구버전 격리·preflight 하위폴더화 (상세 `sessions/INDEX.md §3`).
3. **본 지도 유지**: 신규 문서·폴더 추가 시 §2·§3 갱신.
