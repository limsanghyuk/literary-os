# EXT6 Phase-1 · 비밀의숲 ep01 · 클로드측 blind 독립 저작 — 집 컴퓨터 이어작업 핸드오프 (v1)

- 작성: 2026-07-14 · Claude(Opus, 회사 세션)
- 대상: 집 컴퓨터(저연산 실행 모드) — 아래 산출물을 조사·분석하고 다음 단계를 진행
- 원칙: Stage01~04 SSOT 불변경 · 정본 승격/전면 코퍼스 확장 금지 · ep01 κ 확인 전 ep02–16 대량저작 금지

---

## 0. 한 줄 요약
앵커 **비밀의숲 ep01**에 대해 EXT6 Phase-1 3계약(EntityBridge·CastPresence·CharacterLoad) + CoverageLedger를 **블라인드 독립 저작**하고, 결정론 **Gate A + Gate B를 ERRORS 0**으로 통과시켰다. GPT는 아직 동일 회차를 독립 저작하지 않았다(κ 대조 미실시). 파이프라인 전 구간이 재현 가능한 코드로 봉인되어 있다.

## 1. 오늘 완료한 것
1. **결정론 검증기 신설** `_ext6_tools/ext6_gate_ab.py` — Gate A(§8 7항) + Gate B(§9 6항). `sys.exit(ERRORS수)`.
2. **결정론 파생기** `_ext6_tools/ext6_derive_load.py` — CastPresence→CharacterLoad(§5/§6) 100% 무LLM. (work_id를 회차키가 아닌 작품키로 정정)
3. **ep01 저작 파이프라인 실행**: 원문(corpus) 증거 매칭 → Sonnet 3-에이전트 병렬 CastPresence(블록 1-24/25-48/49-72) → Opus fan-in 정규화(EntityBridge, 이름변이 canonicalize) → 결정론 CharacterLoad 파생 → Gate A/B.
4. **결과**: `[gate] 비밀의숲_01: bridge=25 cast=177 load=25 scenes=72 · ERRORS 0 (Gate A + Gate B PASS)`.
5. **Claude 독립 설계안 봉인** `docs/proposals/CLAUDE_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md` (GPT 문서 미열람 상태 = 진짜 블라인드).

## 2. 산출물 인벤토리 (허브 경로 = 로컬 C:\claude\db\seqcard_ko 동일)
| 아티팩트 | 허브 경로 | 행수 | sha256(앞12) |
|---|---|---|---|
| EntityBridge(9키) | `seqcard_ko/authored_bridge/비밀의숲.bridge.jsonl` | 25 | 7062aaf80a54 |
| CastPresence(10키, 씬×인물) | `seqcard_ko/authored_cast/비밀의숲_01.cast.jsonl` | 177 | 04939c10bbff |
| CharacterLoad(17키, 결정론) | `seqcard_ko/derived_character_load/비밀의숲_01.load.jsonl` | 25 | a294974b7eea |
| CoverageLedger | `seqcard_ko/_ext6_audit/비밀의숲_01.castcoverage.json` | — | annotated 68·empty 4·unresolved 0·union 72 |
| 파생기 | `seqcard_ko/_ext6_tools/ext6_derive_load.py` | — | — |
| 게이트 | `seqcard_ko/_ext6_tools/ext6_gate_ab.py` | — | — |
| Claude 독립안 | `docs/proposals/CLAUDE_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md` | — | — |

입력(불변, 이미 허브 존재): `seqcard_ko/authored/비밀의숲_01.seqcard.jsonl`(72씬 SSOT), `authored_seq/비밀의숲_01.seqblueprint.jsonl`, `authored_arc/비밀의숲_01.episodearc.json`.

## 3. 재현 방법 (집 컴퓨터에서 그대로 실행)
```bash
cd <repo>/seqcard_ko
# (1) 결정론 파생 재생성
python3 _ext6_tools/ext6_derive_load.py . 비밀의숲 1
# (2) 하드게이트 (ERRORS 0 == 통과, exit code = ERRORS 수)
python3 _ext6_tools/ext6_gate_ab.py . 비밀의숲 1
```
기대 출력: `ERRORS 0  (Gate A + Gate B PASS)`. 재파생 diff(A7)가 0이면 CharacterLoad 17필드 전부 CastPresence로부터 결정론 복원됨을 의미.

## 4. 품질 근거 (Gate C, advisory)
band 분포: DOMINANT 1 · MAJOR 2 · MINOR 8 · CAMEO 14 (총 25인물).
| 인물 | band | scene_share | present | focal | speak | 극작 해석 |
|---|---|---|---|---|---|---|
| 황시목 | DOMINANT | 0.6667 | 48 | 41 | 21 | 주인공(전 회차 견인) |
| 강진섭 | MAJOR | 0.3194 | 23 | 10 | 12 | 용의자-운전기사 |
| 한여진 | MAJOR | 0.3194 | 23 | 11 | 15 | 형사 투톱 |
| 박무성母 | MINOR | 0.1667 | 12 | 2 | 9 | 피해자 모친 |
| 박무성 | CAMEO | — | 5 | 0 | 0 | 피해자(시신+사진, 무발화) |
act_placement가 EpisodeArc act_structure(설정/전개/심화/회말전환)와 정합. 피해자가 present>0·focal 0·speaking 0으로 나오는 것은 계약이 "등장(시신/회상)"과 "초점/발화"를 올바로 분리함을 보여줌.

## 5. GPT측 상태 (κ 대조 전제)
- 허브 `docs/external/GPT_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md` + `..._TRANSFER_NOTICE_v1.md` = GPT의 **설계안**만 전달됨(상태 `GPT_INDEPENDENT_DRAFT_LOCKED`).
- **GPT는 아직 비밀의숲 ep01 CastPresence/Bridge/Load 실데이터를 저작하지 않음.** 따라서 κ 대조는 미실시.
- 블라인드 규율: Claude 독립안은 GPT 문서를 열지 않고 봉인함. 교차검토(diff 매트릭스)는 양측 봉인 이후에만.

## 6. 자가감사 결함(수정 대기)
- **B7 인물성 결함**: `비밀의숲:112상황실`(장소/기관)이 인물로 EntityBridge/CastPresence에 등록됨. 현재 Gate B에는 인물성 체크가 없어 통과됨. → 독립안 §7에 **신규 게이트 B7**(character_key가 장소/소품/기관이면 ERROR) 제안 반영. 집에서 B7 구현 시 `112상황실` 행 정리(장소로 재분류 또는 제거) 후 재-derive/재-gate 필요.
- 경계사례: `실무관` 등 역할명 인물, "112상황실 형사들" 같은 집합 인물 → 후속 `is_collective` 플래그 제안(파일럿은 개별 인물만).

## 7. 다음 단계 (권고 순서)
1. **(권고 A) κ 대조 우선**: GPT에 동일 동결계약으로 비밀의숲 ep01 blind 독립 저작 지시 → 두 산출 봉인 후 §10 5단 비교. 대상 필드 = presence_mode/focality/speaking_status(씬×인물 grain) + scene_share_band(인물 grain). 판정: κ<0.4 계약결함 / 0.4–0.6 부분보정 / ≥0.6 안정. **κ≥0.6 확인 전 ep02–16 대량저작 금지.**
2. **(B) B7 게이트 반영**: ext6_gate_ab.py에 B7 추가 + `112상황실` 처리 + 재검증(ERRORS 0 유지 확인).
3. **(C) 확장**: κ 안정 확인 후에만 비밀의숲 ep02–16 → 시크릿가든(앵커2) → 베토벤바이러스(앵커3, 군상극).
4. CrossProviderComparisonRecord(독립안 §6, 12키: po/pe/kappa 등)로 κ 결과를 원장화.

## 8. 경계·미승인 (반드시 유지)
- 정본 승격 금지 · 전면 코퍼스 확장 금지 · Stage01~04 불변경.
- 본 push는 사용자 명시 지시("허브에 로드하라")에 따른 핸드오프 로드이며, 정본 승격이 아님.
- κ 대조/합의/사용자 승인 전에는 계약 동결값 변경·대량 저작 금지.

---
_by: Claude(Opus) · 근거 커밋: 본 문서와 함께 push되는 seqcard_ko/_ext6_* 아티팩트 · Gate: ext6_gate_ab.py ERRORS 0_
