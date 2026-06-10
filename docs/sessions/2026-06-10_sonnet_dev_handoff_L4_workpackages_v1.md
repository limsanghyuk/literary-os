# 저연산 개발 핸드오프 v1.0 — WP 묶음 실행 명세 (V746~V760, Sonnet 4.6 전용) (2026-06-10)

**대상**: 저연산 개발 모드(Sonnet 4.6). 본 문서 하나로 V746~V760 전체를 **외부 문의 없이** 실행 가능해야 한다.
**기준선**: HEAD `5619a9c` · 설계 정본: P1-P5 보강(06-10 `4f28525`) + EFG 보강(06-10 `5619a9c`) · 본 문서가 둘의 **구현 번역본**.

═══════════════════════════════════════════
## §0. 비용 원칙 — 버전별이 아니라 WP(작업 패키지)별
═══════════════════════════════════════════
개발자 지시: 고연산(기획 모드)이 버전마다 개입하는 것은 비용 부적합. 따라서:
1. **V746~V760을 5개 WP로 묶는다.** 고연산 모드 개입 지점은 **WP 경계 0~1회**(WP 완료 보고 검토)뿐이며, 그것도 에스컬레이션 사유 없으면 생략 가능.
2. **Sonnet의 자가 검증으로 WP를 닫는다**: 각 WP의 DoD(아래)는 pytest+게이트로 기계 판정 — 사람·고연산 판단 불요.
3. **Sonnet 재량 범위(사전 승인)**: 내부 헬퍼·프라이빗 함수명·테스트 픽스처 구성·에러 메시지 문구. **재량 밖(변경 금지)**: 공개 시그니처·임계값·DDL·게이트 이름·공식 수식 본체.
4. **에스컬레이션 3조건**(이때만 고연산 복귀): ①공개 인터페이스 변경이 불가피 ②동일 게이트 2회 연속 실패 ③실측 결과가 설계 가정과 모순(예: 패리티 게이트 대폭 미달).
5. WP 내 V버전 부여는 Sonnet이 진행 순서대로 자율 태깅(아래 권장 맵은 가이드).

## §0.5 필수 선행 규약 (불변)
- **모든 WP 시작 전 PREFLIGHT 필수**: `python tools/run_preflight.py` (V431+ 규약). 실패 시 작업 금지.
- 커밋: `feat(wp-N): ...` / 문서는 `docs(sessions): ...`. **docs/sessions/는 .gitignore — `git add -f` 필요.**
- 키는 환경변수로만(`OPENAI_API_KEY` 등), 코드·커밋에 평문 금지. 현재 OpenAI만 가용.
- LLM 호출 코드는 전부 `cost_cap` 파라미터 필수(기본 $1.00/실행, 초과 시 중단+부분결과 저장).
- 전사 원문은 `local_transcripts/`(.gitignore 추가, WP-2)에만 — 허브 커밋 절대 금지.

═══════════════════════════════════════════
## WP-0 — 무결성 마감 (권장 V746) · 규모 소
═══════════════════════════════════════════
**목적**: SP-E.0 일회 실행(8d0edc7)을 재발 불가능 구조로 (P1-R1~R4).
**파일**:
- `tools/run_release_gate.py`: 최종 단계에 `G_INTEGRITY_MANIFEST` 추가 — ①`tools/generate_sha256sums.py`의 생성 함수 호출(스크립트 직접실행 말고 import — 필요 시 함수로 리팩토링) ②전 항목 자기검증 ③`tools/generate_test_inventory.py` 재생성 후 카운트 일치 확인. 실패 시 exit≠0.
- 서명: minisign 부재 환경 고려 — `SHA256SUMS.txt.minisig` 존재 시 검증, 부재 시 **WARN(차단 아님)** + 보고서에 기록. 개발자 키 발급은 개발자 액션(README_RELEASE.md에 1단락 안내 추가).
**테스트** `tests/gates/test_integrity_manifest.py`:
`test_gate_regenerates_manifest` · `test_self_verify_passes_on_clean` · `test_stale_entry_blocks_release` · `test_inventory_count_mismatch_blocks` · `test_missing_sig_warns_not_blocks`
**DoD**: 위 5 테스트 green + `python tools/run_release_gate.py --verify-only` 클린 PASS.

═══════════════════════════════════════════
## WP-1 — validation/ 상설화 + 공식 생애주기 (권장 V747~V750) · 규모 중
═══════════════════════════════════════════
**목적**: tools/formula_validation/*(임시 스크립트, sys.path 하드코딩)를 정규 모듈로 승격. ~25공식 일괄 검증의 상설 인프라.
**파일** (신규는 `literary_system/validation/` 하위):
```python
# formula_registry.py
class FormulaEntry(TypedDict):
    formula_id: str          # 'F-06_fitness' 등 — 공식 ID는 Claude 트랙 정본 표기
    domain: str              # physics|drse|nie|longform|trajectory|emotion|prose|constitution
    score_fn: Callable[[SceneRow], float]   # scene_feature 행 → 점수
    lifecycle: Literal['candidate','validated','recalibrate','deprecated']
REGISTRY: dict[str, FormulaEntry]   # 1차 등록: physics 5(fitness+4계수)·DRSE·이후 도메인별 추가

# stage_registry.py  — 사전등록 임계(변경은 별도 커밋+사유 의무)
STAGES = {
 1: dict(gt='quality_proxy',  metric='spearman', tau=0.40, min_n=30),
 2: dict(gt='plant_payoff',   metric='spearman', tau=0.40, min_n=20),
 3: dict(gt='payoff_actual',  metric='f1',       tau=0.60, min_n=1_work),   # P1-P5 보강 §4
 4: dict(gt='panel_median',   metric='spearman', tau=0.40, min_n=30),
 5: dict(gt='labeled_curves', metric='dtw_pct',  tau=0.30, min_n=2_works),
 6: dict(gt='blind_pref',     metric='spearman', tau=0.50, min_n=30),
}

# formula_harness.py  — tools/formula_validation/harness.py 로직 승격(경로 하드코딩 제거)
class Harness:
    def run(self, stage_id: int, db_path: str, cost_cap: float = 1.0) -> StageReport: ...
# StageReport: formula_id별 {metric, n, pass, lifecycle_suggestion} + JSON 직렬화

# ledger.py — 생애주기 원장
def record(formula_id, event, evidence_path) -> None   # docs/formula_ledger.md에 append(이 파일은 커밋 대상)
def transition(formula_id, new_state) -> None           # 2회 연속 미달→deprecated 후보 자동 표기
```
- CLI: `tools/run_formula_validation.py --stage N --db data/tristore.db [--cost-cap X]`
- 기존 `tools/formula_validation/*.py`는 삭제하지 말고 `_archive/` 이동(이력 보존).
**테스트** `tests/validation/test_formula_harness.py` (synthetic fixture로 LLM 불요):
`test_registry_loads_physics_formulas` · `test_stage1_report_structure` · `test_preregistered_tau_immutable_in_code`(임계가 코드 상수임을 검증) · `test_ledger_append_and_transition` · `test_two_consecutive_fails_marks_deprecated_candidate` · `test_cost_cap_aborts_gracefully`
**DoD**: 6 테스트 green + `--stage 1`이 기존 scenes_5works.jsonl 마이그레이션 데이터로 06-07 결과(ρ≈0.70)를 ±0.02 내 재현(회귀 검증).

═══════════════════════════════════════════
## WP-2 — 트라이스토어 정본 DDL + 전사 인입 (권장 V751~V753) · 규모 중
═══════════════════════════════════════════
**목적**: P1-P5 보강 §3.1 DDL을 정본화, corpus_seed→단방향 마이그레이션, 개발자 전사물 인입 CLI.
**파일**:
- `literary_system/storage/tristore_schema.sql`: **P1-P5 보강 §3.1의 DDL 전문을 그대로**(work/scene/scene_feature/plant_payoff + verbatim_stored=0 CHECK + 인덱스). 임의 수정 금지(재량 밖).
- `tools/tri_store/init_db.py`: 스키마 적용 + `--migrate-seed data/corpus_seed/` (단방향, seed는 read-only 격하 — README에 명시).
- `tools/tri_store/ingest_transcript.py`: `local_transcripts/*.md`(전사 SOP 양식: 씬헤딩/지문/대사 + 메타블록) 파싱 → scene 행(synopsis는 구조 요약 자동 생성 — LLM 1회 호출, cost_cap) + scene_feature 13필드(LLM 추출, annotator='llm:gpt-4o') 적재. **원문 텍스트는 DB에 절대 미저장**(synopsis만) — 테스트로 강제.
- `.gitignore`에 `local_transcripts/` 추가.
**테스트** `tests/storage/test_tristore_canonical.py`:
`test_schema_applies_clean` · `test_verbatim_check_constraint_rejects` · `test_seed_migration_row_counts` · `test_ingest_parses_sop_format`(픽스처 가짜 전사 사용) · `test_ingest_never_stores_raw_text`(DB 전체에서 픽스처 대사 문자열 부재 grep) · `test_provenance_required`
**DoD**: 6 테스트 green. 실 전사물 인입은 개발자 파일 제공 시(블로킹 아님 — 픽스처로 DoD 충족).

═══════════════════════════════════════════
## WP-3 — EmbeddingProvider + DRSE 전환 (권장 V754~V756) · 규모 중
═══════════════════════════════════════════
**목적**: DRSE TFIDF(0.02)→임베딩(0.71 입증) 전환의 정규 구현 (P1-P5 보강 §4 P3-R2).
**파일** `literary_system/drse/embedding_provider.py`:
```python
class EmbeddingProvider(Protocol):
    provider_id: str
    dim: int
    def embed(self, texts: list[str]) -> 'ndarray': ...
# 구현 3: OpenAIEmbedding('text-embedding-3-small') | GeminiEmbedding(키 복구 시) | BGEM3Local(선택적 import — 미설치 시 명확한 안내 에러)
class CachedProvider:   # 데코레이터 — key=(provider_id, model_rev, sha1(text)), 디스크 캐시 data/emb_cache/
```
- `drse_engine.py`: `SemanticScorer`에 provider 주입 생성자 추가(기존 TFIDF는 폴백 유지·기본값은 Embedding).
- 패리티 게이트: `tools/run_emb_parity.py` — 복선 검증셋(validation_scenes_3works.jsonl)에서 BGE-M3 ρ가 기준 provider ρ의 90%↑면 PASS → ledger 기록. **BGE-M3는 10씬 소규모 벤치 먼저**(장비 부하 확인) — 부적합 시 OpenAI 임베딩을 정본으로 하고 에스컬레이션 불요(설계가 허용).
**테스트** `tests/drse/test_embedding_provider.py`:
`test_protocol_conformance_all_providers` · `test_cache_hit_no_api_call`(mock) · `test_scorer_with_injected_provider` · `test_tfidf_fallback_when_no_key` · `test_parity_gate_pass_fail_logic`(mock 점수)
**DoD**: 5 테스트 green(전부 mock — 실 API 불요) + 실키 1회 스모크(OpenAI, cost_cap $0.10).

═══════════════════════════════════════════
## WP-4 — 레퍼런스 검증 정식화 + 중재 레코드 (권장 V757~V760) · 규모 중상
═══════════════════════════════════════════
**목적**: refcheck POC 승격(Mode1/Mode2), Arbitration 불일치 레코드(EFG 보강 §2), 학습신호 스키마 선행 고정.
**파일**:
- `literary_system/validation/refcheck.py`: `run_mode2(work_id, db) -> Mode2Report`(공식 on 실제 씬 — LLM 불요, scene_feature에서 직접) / `run_mode1(scene_id, db, providers, cost_cap) -> Mode1Report`(생성 vs 실제, 3페르소나 블라인드 — refcheck_oai.py 로직 승격, **레퍼런스는 반드시 DB의 전사 기반 씬** — LLM 회상 금지를 코드로 강제: reference 인자는 scene_id만 허용).
- `literary_system/validation/arbitration.py`: `DisagreementRecord {scene_id, formula_id, z_formula, z_llm, gap, branch: formula_defect|llm_defect|ambiguous, evidence}` — gap>1.5σ 시 생성, ambiguous는 `data/disagreement_queue.jsonl`에 적재(차후 UI W3 큐의 데이터원).
- `literary_system/learning/signal_schema.py`: `InterventionEvent` dataclass(EFG 보강 §3.2 스키마 그대로) + jsonl append 저장소. **수집만 구현, 학습 실행 없음**(Phase F).
**테스트** `tests/validation/test_refcheck_arbitration.py`:
`test_mode2_runs_without_llm` · `test_mode1_rejects_non_db_reference`(회상 금지 강제) · `test_blind_label_shuffling` · `test_disagreement_branching_3way` · `test_intervention_event_roundtrip` · `test_cost_cap_on_mode1`
**DoD**: 6 테스트 green + Mode2를 픽스처 작품으로 1회 실행해 리포트 생성. **실 명작 Mode2는 개발자 전사물 도착 시**(WP-4 DoD에 비포함 — 데이터 의존 분리).

═══════════════════════════════════════════
## §5. WP 의존 그래프·보고 양식
═══════════════════════════════════════════
```
WP-0 ──독립──┐
WP-1 ────────┼─→ WP-4 (harness·ledger 사용)
WP-2 ────────┤    WP-4 (DB·전사 씬 사용)
WP-3 ────────┘    WP-4 (Mode1 임베딩·패널)
```
- 권장 순서: WP-0 → WP-1 → WP-2 → WP-3 → WP-4. WP-1~3은 상호 독립이라 병렬·순서 교체 가능.
- **WP 완료 보고(각 WP 마지막 커밋에 포함)**: `docs/sessions/2026-MM-DD_wpN_report.md` — ①DoD 체크표 ②테스트 수 변화 ③재량으로 결정한 것 목록 ④에스컬레이션 여부. 이 보고가 곧 고연산 검토 입력(개입 필요 시에만).

## §6. 개발자 체크리스트 (병렬 트랙)
1. 전자책 1권 구매+3씬 전사(`local_transcripts/`, SOP 양식) → WP-2 인입 → WP-4 실 Mode2.
2. minisign 키 1회 발급(WP-0의 WARN 해소).
3. WP 보고 4건 훑어보기(각 5분) — 에스컬레이션 플래그만 확인.

## §7. 자기 점검
- 본 명세의 시그니처는 코드베이스 실측(physics/fitness_score.py·drse_engine.py·tools 구조) 기반이나, Sonnet이 실제 임포트 시 사소한 불일치 가능 — 그 수준의 적응은 재량 범위(공개 시그니처 의미 유지 시).
- Stage3~6 실행은 데이터 도착 의존 — WP-1은 인프라만 깔고 임계를 사전등록 상수로 고정(데이터 없이도 DoD 가능하게 분리한 것이 본 설계의 비용 핵심).
- V버전 번호는 가이드 — 충돌 시 Sonnet이 연속성만 유지하면 됨.

**문서 ID**: LOS-SONNET-HANDOFF-WP-V1.0-2026-06-10 · Sonnet 읽기 순서: 본 문서 → P1-P5 보강(4f28525) → EFG 보강(5619a9c) → 코드 앵커(physics/·drse/·validation/·tools/)
