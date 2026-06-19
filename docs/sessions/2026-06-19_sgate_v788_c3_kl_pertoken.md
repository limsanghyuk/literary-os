# 2026-06-19 SGATE-v788 — c3 구조게이트 실체화 + KL 정합 + per-token 길이정규화 재측정

**한 줄**: Round#2 실측 분석 → 4개 후속(①②③④)을 **코드로 구현·테스트·커밋**. c3 구조 비퇴행이 비로소 실제로 계산되고, KL 임계가 표준(0.50)으로 통일되고, W의 길이 교란을 진단·재측정하는 도구가 들어왔다.
**기준**: 직전 허브 HEAD `3bdd4da`(Round#2 ADOPT-candidate 확정) 위에 적용. **집 로컬에서 이 문서만 읽고 이어서 작업 가능**하도록 작성.

---

## 0. 집 로컬에서 먼저 할 일 (TL;DR)
```bash
git pull                              # 본 커밋 수신
python tools/generate_test_inventory.py        # 환경별 inventory 재확정(권장)
python -m pytest tests/unit/test_v788_pertoken_winrate.py \
                 tests/unit/test_v788_structure_conformance.py \
                 tests/unit/test_v774_loopc_closure.py \
                 tests/unit/test_phase_a_exit.py -q     # 70 passed 기대
```
그 다음 **§5의 GPU 라운드#3 절차**를 실행하면 된다(이번 세션이 GPU 없이 차단 해제까지 깔아둠).

---

## 1. 배경 — 왜 이 작업이 필요했나
Round#2(4070/실 Llama-3.1-8B) 실측: train 224 / held 56쌍, **held W 0.161→0.357 (ΔW+0.196)**, KL/token 0.117(τ=0.50), VERDICT=ADOPT-candidate. 첫 진짜 held-out 일반화. 그러나 분석에서 **3대 교란** 적발:
1. **상수승자**: winner가 held 전수 'ref'(100%) → train 보상정확도 1.0 포화·과적합 위험.
2. **W1<0.5**: 절대값 0.357 — 모델이 여전히 자기 초안을 명작 ref보다 위로 랭크. "명작처럼 쓴다" 미입증.
3. **길이 교란**: ref(~415자) < draft(~597자). sumlogP는 길이 미정규화라 **긴 쪽이 불리** → 짧은 ref가 자동 우세.

동시에 **c3(구조 비퇴행)는 코드상 N/A 자동통과** 상태였음(R 생산자 부재). 이번 세션이 이 둘을 함께 해결.

---

## 2. 구현 산출물 (이 커밋에 포함)

### ① `literary_system/critic/structure_conformance.py` [신규] — c3 R 생산자
- `winrate_gate.c3 = c1∧c2∧c3` 중 c3의 **결손 생산자**. 종전엔 `r_before/r_after=None`이면 자동 통과(=Round#2 result.txt의 `[N/A]`).
- **R_struct** ∈[0,1]: 5가중 결정론 체크 — callback 0.25 / character 0.20 / tension-band 0.20 / plant→payoff 0.20 / function 0.15.
- **R_pair**: after-vs-before STRUCTURE 쌍대 자기비교(MockCritic 기본), 패배율 ≤ 0.5.
- **R_path**: distribution_guard 병리 페널티 비증가.
- `structural_nonregression(before_scenes, after_scenes, rag_refs, critic) -> r_before/r_after/c3_*` → 게이트에 직접 주입.
- SceneBrief 객체/ dict 양쪽 입력 허용.

### ② KL 표준 통일
- `learning/winrate_gate.py`: `TAU_KL_DEFAULT 0.1 → 0.50`(DESIGN-SGATE-v1, KL/token 표준; 실험 τ=0.50과 정합).
- `learning/loopc_closure.py`: import에 `TAU_KL_DEFAULT` 추가, `tau_kl` 기본값을 상수 참조로, **`compute_structural_r()` 메서드** 추가, `run_round(before_scenes=, after_scenes=)`로 R **자동 산출**(비파괴 가산).
- 회귀 1건(`test_v774` tc03, kl=0.5가 새 경계와 동률) → 의도 보존 위해 `kl=0.6`로 갱신.

### ③ per-token 길이정규화 재측정
- `literary_system/learning/pertoken_winrate.py` [신규, GPU 불필요 순수 코어]:
  - `per_token_logp`, `pairwise_winner(scheme='sum'|'pertoken')`, `win_rate`, `length_diagnostic`.
  - scheme='sum'=Round#2 방식(길이 편향 포함), 'pertoken'=logp/토큰수(편향 제거). 두 W를 함께 산출.
- `experiments/pertoken/remeasure_pertoken.py` [신규 스크립트]:
  - (1) 길이 진단[항상]: pairs JSONL의 draft/ref 길이 비대칭 + '짧은 쪽=승자' 귀무모형 승률.
  - (2) per-token 재측정[logp ledger 제공 시]: `W_sum` vs `W_pertoken`.

### ④ 검증
- `tests/unit/test_v788_structure_conformance.py`(10 TC) + `tests/unit/test_v788_pertoken_winrate.py`(12 TC).
- 영향권 전 테스트 통과(focused 70 passed). tests/unit 전체 회귀 무파손(이번 세션 v787 트리 4847 passed).
- `tools/test_inventory.json` 재생성(11,386→11,405; EA-6 staleness 해소 — **단, staleness는 본 변경 이전부터 존재한 SP-E.0 부채였음**).

---

## 3. ★핵심 실측 — 길이 교란은 가설이 아니라 사실
`remeasure_pertoken.py`로 Round#2 held 56쌍 진단:

| 척도 | draft 평균 | ref 평균 | draft−ref | 귀무('짧은쪽=승자') ref승률 |
|------|-----------|---------|-----------|----------------------------|
| char | 593.1 | 424.1 | +169.0 | **0.955** |
| ws-token | 142.3 | 93.9 | +48.4 | 0.929 |

관측 ref 라벨 승률 = **1.000**. 즉 **'더 짧은 텍스트를 고른다'는 자명규칙만으로 라벨의 95.5%가 설명**된다.
→ 보고된 W1=0.357(sumlogP)이 **길이 인공물일 위험이 크다**. 길이정규화 후에도 ΔW>0이어야 진짜 향상.

---

## 4. 게이트 의미론 변화 (집에서 반드시 인지)
- 이전: c3는 항상 통과 → 게이트가 사실상 c1∧c2.
- 이후: 생성 씬을 `run_round(before_scenes=, after_scenes=)`에 넘기면 c3가 **실값**으로 계산되어 ADOPT 차단 가능.
- **주의**: 씬을 안 넘기면 r_before/r_after는 여전히 None→자동통과(하위 호환). c3를 켜려면 생성 본체(T3 7-pass) 출력 씬을 연결해야 함.

---

## 5. ★GPU 라운드#3 절차 (집/4070에서 차단 해제)
1. **상수승자 완화**: epochs 3→1 + 패널(critic ensemble) 유래 **draft-win / tie 쌍 주입** → winner 분포 다양화.
2. **logp ledger 방출**: 학습/평가 시 행마다 아래 JSONL 저장(이게 ③의 입력):
   ```json
   {"draft":{"sumlogp":-120.3,"n_tokens":142},"ref":{"sumlogp":-90.1,"n_tokens":94}}
   ```
3. **길이정규화 재측정**:
   ```bash
   python -m experiments.pertoken.remeasure_pertoken \
       --pairs pairs_held.jsonl --logp logp_held.jsonl
   ```
   `W_pertoken`이 0.5를 넘고 `W_sum` 대비 ΔW가 유지되면 '길이 무관 향상' 입증.
4. **c3 켜기**: 생성 씬을 loop-C `run_round`에 연결 → 구조 비퇴행을 실제 게이팅.

---

## 6. 변경 파일 목록
```
신규  literary_system/critic/structure_conformance.py
신규  literary_system/learning/pertoken_winrate.py
신규  experiments/pertoken/{__init__.py,remeasure_pertoken.py}
신규  tests/unit/test_v788_structure_conformance.py
신규  tests/unit/test_v788_pertoken_winrate.py
수정  literary_system/learning/winrate_gate.py        (TAU_KL_DEFAULT 0.1→0.50)
수정  literary_system/learning/loopc_closure.py       (compute_structural_r + run_round 씬 주입 + τ 상수참조)
수정  tests/unit/test_v774_loopc_closure.py           (tc03 kl 0.5→0.6)
재생성 tools/test_inventory.json                       (11,405)
```

## 7. 데이터 원칙
명작 verbatim(`ref` 본문)은 **길이·통계만** 사용. 본문 비노출·비커밋 유지(이 문서·코드·테스트 어디에도 원문 없음).
