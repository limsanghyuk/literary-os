# 2026-06-19 종합 핸드오프 — 실 4070 loop-C 실측 + 회사 로컬 이어가기 가이드

> 목적: 오늘(집 4070) 진행한 **모든 내용·방식·결과**를 체계 정리. **다음 작업은 회사 로컬에서 이어서** 진행.
> 보안: verbatim 명작 원문·API 토큰 비포함. 선호쌍 데이터·킷 코드는 로컬 전용(아래 7장).

## 0. TL;DR — 현재 위치
- 샌드박스 GPU 부재로 막혀 있던 **실 GPU loop-C 학습 라운드**를 집 RTX 4070에서 처음 완주.
- **라운드 #1**(24쌍, in-sample): 메커니즘 실증(dM +16.07), 채택 보류(in-sample·KL/구조 미측정).
- **라운드 #2**(224 train / 56 held-out): 진행 중. held 베이스라인 W0(acc)=0.161 측정 = *학습 전 Llama는 명작보다 매끈한 일반 산문을 선호*(좁혀야 할 격차). 사후 W1/dW·KL은 학습 종료 시 확정.
- 다음: held dW·KL 확정 → 채택 후보면 구조게이트(공식 채점) → G_LOOPC_WINRATE 완전 판정.

## 1. 오늘 한 일 (타임라인)
1. 실 4070에서 train_4070.py 실행 시도 → 4개 블로커 진단·해결(2장).
2. 라운드 #1 완주(Llama-3.1-8B, 24쌍) → dW=0 / dM+16.07 (3장).
3. 게이트 정직 판정: 메커니즘 PASS / 채택 보류(4장).
4. 수백 쌍 데이터 파이프라인 구축(명작 닻, 280쌍, 80/20) (5장).
5. train_4070 v3 작성(held-out dW + KL proxy + rounds_ledger) → 라운드 #2 실행(진행 중).
6. 본 핸드오프 + 세션 문서 허브 푸시.

## 2. 확정 동작 스택 + 진단 체인 (재현 필수)
**스택**: Windows / Python 3.10 / **torch 2.6.0+cu124** / transformers 5.12.1 / trl 1.6.0 / peft 0.19.1 / bitsandbytes 0.49.2 / datasets 5.0.0 / numpy 2.2.6. 모델 meta-llama/Llama-3.1-8B-Instruct(게이트 승인+토큰). 4bit nf4 + QLoRA(q/k/v/o_proj, r16, beta0.1, lr5e-5).

**블로커 4종 → 해결**:
1. `huggingface-cli not found` → hub 1.x CLI는 `hf`. HF_TOKEN env로 우회.
2. import 무음 네이티브 크래시(0xC0000005) = OpenMP/MKL 다중런타임 → 환경변수 `KMP_DUPLICATE_LIB_OK=TRUE`,`MKL_THREADING_LAYER=GNU`,`MKL_SERVICE_FORCE_INTEL=1`,`OMP_NUM_THREADS=1`. 진단=각 import를 별도 subprocess 누적 실행으로 격리.
3. `cannot import name 'FSDPModule'` = **trl 1.6은 torch 2.6+(FSDP2) 요구** → torch 2.5.1→2.6.0+cu124 업그레이드(4070 드라이버 cu124 호환).
4. `401 GatedRepoError` → HF 토큰 주입 + Llama 게이트 승인.
- 파일툴 virtiofs 대용량 쓰기 truncate → heredoc→/tmp→cp 패턴.
- 마운트 캐시가 라이브 진행을 반영 못 함(샌드박스에서 진행률 모니터 불가) → 콘솔/작업관리자 GPU로 확인.

## 3. 라운드 #1 결과 (24쌍, 3에폭, in-sample)
| 지표 | 전 | 후 | |
|---|---|---|---|
| abs-pref-acc | 0.458 | 0.458 | dW +0.000 (절대순서 둔감) |
| reward-margin | +27.70 | +43.77 | **dM +16.07 — 학습 확정** |
| rewards/margins | 0.281 | 1.331 | DPO 내부 4.7배 |
| rewards/accuracies | 0.575 | 1.000 | |
해석: DPO가 최적화하는 상대선호(마진) 결정적 상승. dW=0은 지표 둔감이지 무변화 아님. **단 in-sample → 일반화 증거 아님**.

## 4. 게이트 판정 논리 (G_LOOPC_WINRATE)
조건 = ΔW>0 ∧ KL≤τ ∧ 구조 비퇴행. 라운드 #1: ΔW in-sample만, KL·구조 미측정 → **채택 보류**. 게이트가 과적합을 정직하게 거름(tiny-gpt2/OpenAI 6지표와 동일 패턴, 단 이번은 실 8B/4070 인프라 완전 실증).

## 5. 데이터 파이프라인 (라운드 #2)
self-preference 편향 제거 위해 **LLM 심판 제거, 명작 정적 닻**(ADR-243 M2):
- chosen=실제 명작 씬(corpus_ko 41,506 사용가능 풀, 250~650자), rejected=gpt-4o-mini draft.
- 280쌍(고유 명작 171, 7기능×6장르), 중복 제거, **결정적 80/20 → train 224 / held 56**.
- 생성: 샌드박스 스레드 병렬 + 시간분할(백그라운드 프로세스가 호출 종료 시 소멸 → 포그라운드 청크).
- held 베이스라인 W0=0.161, M0=-242.61: 학습 전 모델은 명작<일반산문 선호 = 격차 정량.

## 6. train_4070 v3 — held-out 측정
- train 학습 → **held(미학습 56쌍)에서 W0→W1, M0→M1** = 진짜 일반화.
- **KL/token proxy**: held chosen에서 adapter-ON(정책) vs disable_adapter()(기준) per-token KL 평균, τ=0.50.
- 판정 출력 `[dW>0]`,`[KL≤τ]`, 구조비퇴행은 literary_system 게이트 위임. dW>0∧KL≤τ → ADOPT-candidate.
- **rounds_ledger.jsonl** 자동 누적(ts·W0/W1/dW·M·KL·verdict·어댑터경로).

## 7. 산출물 위치 (★중요)
| 무엇 | 위치 | 허브? |
|---|---|---|
| 학습된 가중치(ΔW) | `4070_oneclick/lora_out_4070/adapter_model.safetensors`(27MB) | ✗ 로컬 |
| 라운드 장부 | `4070_oneclick/rounds_ledger.jsonl` | ✗ 로컬 |
| 수치 결과 | `4070_oneclick/result.txt` | 수치만 본 문서에 |
| 선호쌍(verbatim 포함) | `4070_oneclick/pairs_train.jsonl`·`pairs_held.jsonl` | ✗ **비커밋(원문 포함)** |
| 킷 코드 | `4070_oneclick/{RUN_TRAIN,train_4070,make_pairs}` | 커밋 가능(verbatim 아님) |
| 입력 코퍼스 | `db/corpus_ko/scenes` | ✗ 로컬 |
| 방법론·수치 | `docs/sessions/2026-06-19_*` | ✓ 푸시됨 |

## 8. 다음 작업 — 회사 로컬 이어가기 (runbook)
회사 PC=노트북 약GPU → 셋 중 선택:
- **옵션 A (분석 이어가기)**: 집 4070의 `rounds_ledger.jsonl` + `lora_out_4070/` 어댑터를 회사로 복사 → held 결과 검토·다음 데이터 설계. GPU 불요.
- **옵션 B (클라우드 학습)**: RunPod 키 확보 시 CloudTrainingNode(V786, PresignedHttpStore 암호화·자동삭제)로 클라우드 라운드. **키 미제공이 현재 차단점**.
- **옵션 C (구조게이트 통합)**: 채택 후보 시 생성 샘플에 공식 채점(drama_genre_drse 등) 돌려 구조 비퇴행 확인 → G_LOOPC_WINRATE 완전 판정 → LoopCClosure/LOSDB 정식 레지스트리로 어댑터 승격(현재 standalone 킷은 분리됨).

권장 순서: A로 라운드 #2 결과 확정·해석 → C로 구조게이트 1회 → 데이터 추가 확대(NextEpisodeBench 은닉GT) → B(클라우드)로 규모 확장.

## 9. 보안/프로토콜
- 토큰(GitHub/OpenAI/HF) env 전용·미저장·sed 마스킹, 푸시 후 remote 토큰 제거. HF 토큰 채팅 노출분 폐기·재발급 권고.
- verbatim 비커밋. docs/sessions는 git add -f.
- 매 버전 RULE-0 Preflight + 통합 ZIP(literary_system 정식 버전에 한함; 본 킷은 실험 스캐폴드).

관련: 2026-06-19_real_4070_dpo_round_and_scaled_data, 2026-06-19_install_4070_train_design, 2026-06-18_real_6metrics.

## 10. 라운드 #2 최종 결과 (확정, 2026-06-19)
**held-out 56쌍 (미학습)** — 라운드 #1과 결정적 차이: 진짜 일반화.
| 지표 | 전 | 후 | Δ |
|---|---|---|---|
| abs-pref-acc | 0.161 | 0.357 | **dW +0.196** |
| reward-margin | -242.61 | -80.1 | dM +162.5 |
| KL/token | — | 0.117 | τ=0.50 |

G_LOOPC_WINRATE: `[PASS]` dW>0(held 일반화) · `[PASS]` KL≤τ(0.117≪0.50, 비해킹) · `[N/A]` 구조비퇴행 → **VERDICT: ADOPT-candidate**.
해석: 명작 선호 16%→36%(2배+), 마진 -243→-80. **실 8B/4070에서 일반화 ΔW 첫 확보**. 단 절대값 36%(아직 역전 전)·마진 음수 → 데이터/에폭 추가로 추가 전진 여지. 최종 채택은 구조게이트(옵션 C) 통과 후.
어댑터=`lora_out_4070/adapter_model.safetensors`(C:\claude, 로컬). 장부=rounds_ledger.jsonl 1행.

## 11. ★정정 (2026-06-20) — 10장 무효: per-token 재측정 결과
10장의 "ADOPT-candidate"는 **per-token 재측정으로 무효(LENGTH ARTIFACT)**. 저장 어댑터로 held 56쌍 ledger 방출(학습없이)·길이정규화 재측정:
- sum(길이편향) W 0.161→0.357 (+0.196) vs **per-token W 0.000→0.000 (+0.000)**. dW+0.196은 전적으로 길이착시(ref 424자<draft 593자). per-token 마진만 -1.51→-1.08(+0.434, 임계미달).
- **G_LOOPC c1 per-token FAIL → ROLLBACK(어댑터 폐기)**. 상세=`docs/sessions/2026-06-20_pertoken_remeasure_result.md`. 재현=`tools/loop_c_4070_kit/REMEASURE.bat`.

### 회사에서 다음 작업 (확정 우선순위 — DELIBERATION-v1 §3)
1. **페어링 재설계** 믹스 15/55/20/10: P1(등급화 열화·**길이매칭**) / **P3(AI 초고끼리·암기위험0·주력)** / P2(온폴리시) / P4(동점). 모든 쌍 길이매칭 + `learning/memorization_gate.py`(E4) 통과 + **작품단위** train/held 분리.
2. 학습 시 **logp ledger(sumlogp+n_tokens) 방출** → **per-token으로만 ΔW 판정**(sum 금지, ADR-LADDER-3). held≥250.
3. **c3 구조게이트 켜기**: 생성 씬을 loopc_closure `run_round(before_scenes=, after_scenes=)`에 연결.
4. 광역 아크 목표는 DPO 밖 → 계층 플래너 별도 트랙(DESIGN-HIER-PLANNER 미착수).
관련 최신 코드(git pull로 수신): `critic/structure_conformance.py`·`learning/pertoken_winrate.py`·`learning/memorization_gate.py`, 설계=DESIGN-LLM-LADDER-v1·DESIGN-DATA-EVAL-DELIBERATION-v1.
