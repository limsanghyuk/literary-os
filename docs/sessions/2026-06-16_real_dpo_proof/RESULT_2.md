# 진짜 학습 실측 #2 — 실 LLM 선호쌍 → 로컬 DPO (Mock·합성 아님)

실행: 2026-06-16 · 데이터: **gpt-4o-mini가 직접 생성+판정한 선호쌍 6건** · 학습: tiny-gpt2 CPU DPO 10ep

## 파이프라인 (모두 실제)
1. 실 LLM(gpt-4o-mini)이 6개 드라마 시드마다 두 문체(A 긴장·여백 / B 평이) **실제 생성**
2. 실 LLM이 **판정**(더 우수한 쪽) → chosen/rejected 라벨 (= loop-C·LLM-1 critic 실측)
3. 그 실 선호쌍으로 **로컬 모델 DPO 학습** (LLM-0: 생성기 가중치는 로컬 소유)

판정 분포: A(긴장·문학 문체) 6 / B 0 — 판정기가 의도 방향으로 일관 식별.

## 결과 (실측)
| 지표 | 학습 전 → 후 |
|---|---|
| DPO 손실(궤적) | 0.6822 → 0.6293 (단조 감소 ✅) |
| **DPO 보상마진** | **0.0223 → 0.1324 (약 6배 ↑)** |
| DPO 보상정확도 | 0.7 → **1.0** |
| 로그확률 마진(chosen−rejected) | −25.19 → −23.80 (Δ +1.38) |
| 선호정확도(이산) | 0.67 → 0.67 (tiny-gpt2 용량 한계) |

→ **실 LLM 신호로 로컬 모델이 실제 학습.** 보상마진 6배·보상정확도 1.0 = chosen 일관 선호 강화.

## 실측 #1 대비
- #1: 합성 데이터 → 보상정확도 1.0, 선호정확도 0.70→0.80
- #2: **실 LLM 생성+판정 데이터** → 보상마진 0.022→0.132(6배), 보상정확도 0.7→1.0
- 공통: DPO 손실 단조 감소. **RLAIF 메커니즘이 실/합성 양쪽에서 실작동 확인.**

## 한계 (솔직히)
- 모델은 여전히 tiny-gpt2(장난감). 실 드라마 생성기(3B/8B)는 GPU 필요(4070/실 클라우드).
- 6쌍은 적음 — 이산 정확도까지 뒤집으려면 데이터 확대+반복.
- 보안: API 키는 환경변수로만 사용, **어떤 파일에도 저장·커밋하지 않음.** 스크립트는 OPENAI_API_KEY env에서 읽음.

## 재현
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers datasets trl openai
OPENAI_API_KEY=... python gen_pairs_openai.py   # 실 LLM 선호쌍 생성
python train_on_real_pairs.py                   # 로컬 DPO 학습+실측
```
