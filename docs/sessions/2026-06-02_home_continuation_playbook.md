# 집 로컬 이어가기 플레이북 — Phase E 검증 우선 진입
**작성**: 2026-06-02 (Claude 기획·설계 모드) · **기준선**: V745 (v13.0.0) · **허브**: github.com/limsanghyuk/literary-os

본 문서는 회사 환경 세션에서 진행한 내용을 집 로컬에서 그대로 이어가기 위한 단일 인계 문서다.

---

## 0. 한 줄 요약
Phase E는 "전부 만들고 검증"이 아니라 **검증을 입구 관문으로 박고**(SP-E.0 무결성 → 저비용 사전실험 → 최소 슬라이스 진짜검증 → go/no-go), 통과 시에만 본격 빌드한다. 현재 핵심 가설(구조+LLM > 순수 LLM)은 **미증명**이며 이것이 단일 분기점이다.

---

## 1. 허브 현재 상태 (커밋·파일 맵)
| HEAD | 내용 | 위치 |
|---|---|---|
| 2b3c3bc | Phase E 보고서 v1.1 (이전) | docs/sessions |
| 5536758 | Phase E~G 통합 기획 v1.0 + 핸드오프 | docs/sessions/2026-06-02_phase_efg_planning_* |
| 96f85eb | 검증 우선 제안서+설계도+핸드오프 | docs/sessions/2026-06-02_phaseE_validation_first_* |
| d3f6622 | 검증 실험 번들 + 세션 정리 | experiments/value_proof/* , docs/sessions/2026-06-02_session_summary.md |
| (본 push) | 본 이어가기 플레이북 | docs/sessions/2026-06-02_home_continuation_playbook.md |

핵심 파일:
- 실험: `experiments/value_proof/harness_one.py` `aggregate.py` `README.md` `results.jsonl`
- 결과: `docs/sessions/2026-06-02_value_proof_MVE_results.md`
- 기획: `docs/sessions/2026-06-02_phase_efg_planning_report_v1.docx`
- 검증설계: `docs/sessions/2026-06-02_phaseE_validation_first_blueprint_v1.docx`

---

## 2. 확정된 방향 — 검증 우선 "입구 관문" 4단계
완전 사전검증은 불가능(진짜 검증엔 최소 코퍼스+LLM-1이 필요 = Phase E 일부). 그래서 분리된 전(前)단계가 아니라 **시간박스+사전등록 임계가 걸린 입구 관문**으로 설계한다.

### Step 1 — SP-E.0 무결성 회복 (선결, 비협상)
V745 매니페스트 stale를 먼저 고쳐야 이후 모든 게이트가 신뢰됨.
- TD-E0-1: release_gate에 "빌드 마지막에 SHA256SUMS·test_inventory 재생성 후 자기검증 PASS" 게이트 추가(G_INTEGRITY_MANIFEST). 미재생성 시 릴리즈 차단.
- TD-E0-2: `tools/generate_test_inventory.py`를 릴리즈 파이프라인에 hook, source_hash 불일치 시 FAIL.
- TD-E0-3: ADR-37·38 파일 복구(INDEX엔 있으나 파일 누락), 83~87·126·127은 "의도적 결번"으로 INDEX 명시(G_ADR_CONTINUITY).
- 검증: `sha256sum -c SHA256SUMS.txt` 해시불일치 0건이어야 함(현재 53건).

### Step 2 — 저비용 사전 실험 묶음 (빌드 거의 불필요)
- 2a. **길이통제판 프록시 MVE 재실행**(experiments/value_proof). 1차 결함=길이 교란(A 874 vs B 557자) 교정.
- 2b. **기존 코드 내부정합 점검**: 전체 테스트가 지금 실제로 green인가, `physics_coefficient_updater` 계수 업데이트가 수렴하는가, 공식 점수가 무언가(길이/판정 등)와 상관되는가.
- 목적: "부족한 부분" 조기 발견·조정.

### Step 3 — 최소 슬라이스로 진짜 검증
- Gold 코퍼스 일부(10~30편) + LLM-1 1팔 최소 연결만 만들어 **arm B = 실제 NKG·공식 파이프라인**으로 G_VALUE_PROOF 실행.
- arm A = 순수 LLM. 동일 프롬프트·동일 길이·동일 토큰예산. 인간 작가 5+ 블라인드 평가.

### Step 4 — go/no-go (임계·시간박스 사전 고정)
- 사전등록 임계(예): B 선호 ≥60%, p<0.05, 효과크기 보고.
- 시간박스(예): Step 2 사전실험 2~3주. 신호 없으면 "더 튜닝"이 아니라 설계 재검토/no-go로 분기.
- **PASS → Phase E 본격 빌드(UI·RLAIF·전체 코퍼스·F·G). FAIL → Critic 재설계.**

> 경고(결정 지연 방지): "정합성이 완벽해질 때까지"는 끝이 없다. 진입 전에 임계와 시간박스를 반드시 못 박을 것.

---

## 3. 집에서 실험 이어가기 (정확한 절차)
제가 회사 환경에서 실행한 방식 그대로.

### 3.1 기본 재실행 (Gemini)
```bash
cd experiments/value_proof
export GEMINI_API_KEY=<본인 키>        # 코드에 키 넣지 말 것
rm -f results.jsonl
for i in 0 1 2 3; do python3 harness_one.py $i; done
python3 aggregate.py
```
설정: 모델 gemini-2.5-flash, thinkingBudget=0, 생성 temp 0.8 / 판정 temp 0.2, 씬별 seed 블라인드.

### 3.2 길이 교란 교정 (우선)
- 양 팔 동일 목표 길이 명시(예: 두 프롬프트 모두 "정확히 350±30자").
- 구조 지시를 user 프롬프트가 아니라 system 분리해 출력 토큰예산 잠식 방지.
- 양 팔 max output tokens 동일하게(현재 A 750/B 820 → 동일값으로).

### 3.3 Claude·GPT로 돌리려면
- **충전 필요**: 연결성은 확인됨(Anthropic 400=크레딧부족, OpenAI 429=쿼터초과 → 네트워크 도달 OK). 잔액만 채우면 접속됨.
- **코드 교체**: `harness_one.py`의 `call()`은 Gemini REST 전용. 프로바이더별 어댑터 추가 필요.
  - Anthropic: POST https://api.anthropic.com/v1/messages, 헤더 x-api-key + anthropic-version, body {model,max_tokens,messages}.
  - OpenAI: POST https://api.openai.com/v1/chat/completions, 헤더 Authorization Bearer, body {model,max_tokens,messages}.
- 강한 모델(Claude/GPT-4급)을 판정자로 쓰면 Gemini flash보다 신호 품질↑.

---

## 4. 열린 결정 (D1~D20) — 집에서 확정 필요
- D1~D8(v1.0): 노선 B / 진입시점 / 코퍼스권리 / UI위치 / 자금 / SP순서 / 범위 V795 / Claude Design.
- D9~D15: 무결성 선결 / 생성완화=초안만 / 다언어 한→영 / 자금 R&D+스튜디오 / 사업트랙 Phase E 병행 / ADR-211 연속 / 자동 롤백.
- D16~D20: 검증우선 채택(G_VALUE_PROOF) / MVE 시점 / 사전등록 임계 / 작가 5+ / 공식진화+ablation.
상세는 docs/sessions의 각 핸드오프·설계도 참조.

---

## 5. 권장 실행 순서 (집에서 바로)
1. (지금 가능) Step 1 SP-E.0 무결성: `sha256sum -c SHA256SUMS.txt`로 53건 확인 → release_gate 보강 → 재생성.
2. (지금 가능) Step 2a 길이통제판 MVE 재실행(§3.2) → aggregate.
3. (지금 가능) Step 2b 테스트 green 여부·계수 수렴 점검.
4. 결정 D1~D20 확정.
5. Step 3 최소 슬라이스(Gold 일부+LLM-1 1팔) → 실제 파이프라인 arm B로 검증.
6. Step 4 go/no-go 판정 → 통과 시 Phase E 본격 빌드.

---

## 6. 핵심 진실 (오해 방지)
"결과가 나온다 = 증명"이 아니다. 세 층위 분리:
- ① 실행됨(runs): ✅ MVE가 끝까지 돌았음.
- ② 무결성·내부정합: ⚠️ 코드 미손상이나 매니페스트 stale, 테스트는 내부규칙만 검증.
- ③ 알고리즘이 실제로 효과 있다: ❌ 미증명(MVE는 프록시·무승부·길이교란).
LLM은 어떤 입력에도 산출물을 낸다 → 산출물 존재는 ①만 증명. ③은 본 실험(실파이프라인+인간평가+길이통제+충분한 N) 통과로만 증명.

---

## 7. 보안 수칙
- 4개 키(GH PAT·Claude·GPT·Gemini)는 환경변수 전용·마스킹·사용 후 unset. 코드/문서/커밋/채팅에 키 노출 금지.
- 현재 Anthropic·OpenAI 잔액 소진, Gemini 사용 가능 상태.
