# 2026-06-21 SP-E.9 라운드#1 — 첫 깨끗한 per-token ADOPT-candidate (4070)

Round#2(길이착시 ROLLBACK) 후속. **길이매칭(tokΔ=0) 깨끗한 쌍**으로 4070 QLoRA DPO 1라운드 → per-token dW>0 첫 실측.

## 데이터 (P0 게이팅 통과)
- P1 graded-degradation(break_causality=문장 셔플, **길이보존**) chosen=원본 명작씬 / rejected=인과셔플본.
- 개발자 `learning/pairing` build() 게이팅: length_match(tokΔ=0 전부통과)·work-level split. **train 681 / held 252(≥250)·누설0**.
- 명작 원문 verbatim은 학습 입력(로컬)만, 본 문서·ledger엔 수치만.

## 결과 (held 252, Llama-3.1-8B QLoRA r16, 2 epoch, ~49분)
| 지표 | W0 | W1 | Δ |
|---|---|---|---|
| per-token 승률 | 0.952 | 1.000 | **dW_pt +0.048** |
| sum 승률(참고) | 0.940 | 1.000 | +0.060 |
| per-token 마진 | 0.184 | 1.018 | +0.834 |
| KL/token | — | 0.406 | τ=0.50 |

**G_LOOPC_WINRATE(per-token): [PASS] dW_pt>0 · [PASS] KL≤τ · [N/A] c3 → ADOPT-candidate.**
Round#2와 결정적 차이: 길이 통제 하에서도 per-token dW 양수 = loop-C가 길이무관하게 모델을 이동.

## 정직한 해석 — 메커니즘 증명이지 craft 증명 아님
1. **베이스라인 0.952**: "일관 vs 셔플"은 base도 95% 맞히는 쉬운 과제. 학습은 잔여 4.8%만 뒤집음.
2. **과적합**: train_loss 3e-6, rewards/margins +26, rejected logprob -37까지 압박. KL 0.406=τ 근접(공격적). → 다음 epochs 2→1.
3. **c3 미측정**: rejected 강압 → 일반 유창성 비퇴행 확인 필요.
4. 졸업(SP-E.10)=5 adopt 중 **1/5**.

## 다음
- ★**P3 안티-LLM craft 쌍**(show-don't-tell vs tell): base가 95%로 시작 안 함 → 기교 학습 진짜 측정. (P3 생성기는 개발자 스텁; API 생성으로 채움)
- epochs 2→1(KL 통제), c3 구조게이트 켜기(생성 씬 연결).
- 누적 5라운드(각 ~50분 4070) → Phase E Exit.

산출: lora_p0/adapter(로컬), rounds_ledger.jsonl 1행. RunPod 불요 — 4070 단독.
