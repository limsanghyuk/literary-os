# 클라우드 실 ΔW 경로 — 실측 발견 (2026-06-19)

기준 v13.40.0. 사용자 질문 "실 ΔW를 클라우드로 해결 가능한가" → 제공 키로 전 경로 실제 시도·확인.

## 결론: 클라우드로 가능하나 **GPU 렌탈 경로(RunPod/Lambda)로만**. LLM 키 파인튜닝은 전부 막힘.

| 경로 | 키 보유 | 시도 결과 |
|---|---|---|
| OpenAI 파인튜닝(DPO/SFT) | ✅ OpenAI | ❌ **403 training_not_available** — "OpenAI is winding down the fine-tuning platform, your org no longer able to create jobs"(플랫폼 종료) |
| Gemini 튜닝 | ✅ Gemini | ❌ **501 not implemented** — 튜닝 가능 모델 0, SDK deprecated |
| Anthropic 파인튜닝 | ✅ Anthropic | ❌ 공개 파인튜닝 API 없음 |
| **RunPod/Lambda GPU** | ❌ **키 없음** | ✅ 가능(인프라 V786 준비됨) — 키만 있으면 owned 3B/8B QLoRA 실 ΔW |
| 로컬 4070 | (개발자 PC) | ✅ 가능(run_4070.bat) — owned, on-thesis |

## 의미 (전략 갱신)
- **LLM 제공사 파인튜닝 API는 더이상 클라우드 학습 수단이 아님**(OpenAI 종료가 결정적). 호스팅 FT로 ΔW 측정하려던 경로 A 폐기.
- 실 가중치 학습 ΔW의 클라우드 경로 = **GPU 컴퓨트 렌탈(RunPod/Lambda)** 단일. 이게 V768/V772/V786이 처음부터 옳았던 이유(LLM FT가 아닌 GPU 직접 임대).
- 따라서 다음 필요 = **RunPod/Lambda 키 1개 + 소액 결제**. 그 외 인프라(암호화 저장·자동삭제·CloudTrainingNode·G_LOOPC_WINRATE)는 완비.
- 대안: 개발자 4070 로컬(키 불필요, owned, on-thesis).

## 준비 완료 (키 도착 즉시 실행)
- 선호쌍: 개발자 dpo_pairs.jsonl 24쌍(+자체평가로 수백 확대 가능).
- 노드: CloudTrainingNode(암호화 업로드→RunPod QLoRA DPO→어댑터 회수→자동삭제→ΔW→수용판정).
