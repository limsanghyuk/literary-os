# V773 설계도 — loop-C 폐회로 실연결 (Closed-Loop Real Training) v1.0

**문서 ID**: LOS-V773-LOOPC-CLOSURE-L4-V1.0-2026-06-16 · **기준선**: HEAD `f49e2fd` V772 / v13.25.0
**작성**: 데이터·검증/설계 트랙 · **대상 구현**: 저연산 개발 모드(Sonnet) · **ADR 제안**: ADR-233

## 0. 왜 V773인가 (연결의 마지막 한 칸)
V765~V772에서 RLAIF 사슬의 *부품*이 전부 코드화됐다: 선호쌍(loop_c) → 보상모델 → 트리거(V765) → 라우팅(V768) → 로컬/클라우드 실 어댑터(V767·V772) → 첫 학습 킷(V771). **그러나 이들이 하나의 닫힌 루프로 자동 연결되어 있지 않다** — 학습 후 "정말 좋아졌나"를 E2E 승률로 되먹여 다음 라운드를 결정하는 **폐회로 글루**가 없다. V773 = 그 마지막 연결.

## 1. 폐회로 정의 (V773가 잇는 8단계)
```
① 선호쌍 풀(dpo_pairs.jsonl)  ← 데이터트랙(Pass7 패널·loop_c·E2E)
        ↓ RLAIFTrigger(V765) → RLAIFTrainingSpec
② 라우팅 ProviderRouter(V768) → {LOCAL 4070 | RUNPOD | LAMBDA}
        ↓
③ 실 학습 LocalGPUAdapter(V767)/RealRunPodAdapter(V772) → QLoRA DPO (first_training_kit V771)
        ↓ 학습된 LoRA 어댑터
④ 재측정 eval_winrate + e2e_pass5_home → 생성 vs 명작 승률 W₁
        ↓
⑤ 수용 게이트 G_LOOPC_WINRATE: ΔW=W₁−W₀ > 0 AND KL_guard 통과 AND 구조게이트 미퇴행
        ↓ pass → 어댑터 채택(레지스트리 등재) / fail → 폐기·롤백
⑥ 결정: 향상 지속 → 선호쌍 확대 요청 → ①로 (다음 라운드)
⑦ 정체/퇴행 → 데이터트랙에 "어느 기능축이 약한가" 피드백(midpoint·setup 등)
⑧ 종료조건: W ≥ 목표(예 0.55→단계적 상향) 또는 라운드 예산 소진
```

## 2. 신규 컴포넌트 (V773 구현 대상)
| 컴포넌트 | 책임 | 기존 재사용 |
|---|---|---|
| `learning/loopc_closure.py` `LoopCClosure` | ①~⑥ 오케스트레이션(1라운드 실행·결과 리포트) | RLAIFTrigger·ProviderRouter·adapter·first_training_kit |
| `learning/winrate_gate.py` `G_LOOPC_WINRATE` | ⑤ 수용 판정(ΔW>0 · KL≤τ · 구조게이트 비퇴행) | eval_winrate·e2e_pass5_home·LOSConstitution |
| `finetune/lora_model_registry` 연동 | 채택 어댑터 버전·메타 등재(롤백 지원) | 기존 registry |
| `tools/run_loopc_round.py` | CLI 1라운드(로컬/클라우드 택), 산출 리포트 | — |

## 3. 수용 게이트 G_LOOPC_WINRATE (정량 기준)
- **1차(필수)**: ΔW = W₁ − W₀ > 0 (학습 후 명작 대비 승률 상승). baseline W₀=0.588(first_training_kit 측정).
- **2차(가드)**: KL(학습모델 ‖ 기준모델) ≤ τ_KL — 과적합·붕괴 방지(DPO β로 통제).
- **3차(비퇴행)**: 구조 게이트(LOSConstitution R) 평균이 학습 전 대비 하락 없음 — 품질 향상이 구조 파괴를 대가로 하지 않음.
- 세 조건 AND → 채택. 하나라도 실패 → 롤백 + 원인 로그.
- ※ 단일 라운드·소수 쌍에선 ΔW가 노이즈 → **최소 N라운드 이동평균** 또는 **씬 표본 확대**를 게이트 신뢰조건으로 명시(통계적 약함 정직 표기).

## 4. LLM-0 경계 준수 (불변)
- 학습 대상 = **생성기**(LLM-0 소유, 로컬 가중치). critic/corpus/constitution는 미접촉.
- 외부 LLM은 ①의 선호쌍 *생성·판정*(loop_c, 이미 LLM-1 허용 영역)에만. 학습 자체는 로컬/자기 클라우드 GPU.
- 선호쌍·실 텍스트는 **로컬 전용**(허브엔 id/winner/기능축만). G_LLM1_BOUNDARY 유지.

## 5. 실행 순서 (개발자 4070 / 클라우드)
1. 스모크: `run_loopc_round.py --pairs sample_dpo_smoke.jsonl --smoke` (파이프라인 무에러 확인).
2. 실데이터 1라운드: `--pairs C:\...\dpo_pairs.jsonl --base meta-llama/Llama-3.2-3B --provider LOCAL`.
3. G_LOOPC_WINRATE 판정 → 채택/롤백 자동.
4. 라운드 리포트(W₀·W₁·ΔW·KL·R) 허브 적재(수치만, verbatim 제외).

## 6. 데이터트랙 ↔ 코드트랙 분업 (이 설계가 고정)
- **데이터트랙(본 모드)**: 선호쌍 품질·규모 확대(명작 베스트씬 큐레이션·대규모 E2E 반복·기능축별 약점 보강), G_LOOPC_WINRATE 기준 정교화.
- **코드트랙(개발자)**: §2 컴포넌트 구현 + GPU 실행.
- 폐회로가 닫히면 둘의 산출이 매 라운드 자동 맞물린다 = "1단계(자율 생성 품질) 진화 엔진" 가동.

## 7. 결론
V773는 새 기능이 아니라 **이미 만든 부품들을 닫힌 학습-측정 루프로 잇는 글루 + 수용 게이트**다. 이게 연결되면 "선호쌍 → 학습 → 명작 대비 재측정 → 다음 라운드"가 자동 순환하며, 생성물을 명작 수준으로 좁히는 1단계 과제가 *반복 가능한 엔진*이 된다. UI/협업(E.3/P5)은 이 엔진이 성숙한 뒤 2단계로 얹는다.
