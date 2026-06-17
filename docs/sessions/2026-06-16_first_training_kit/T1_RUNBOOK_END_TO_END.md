# T1 실행 런북 — 설치부터 산출물 처리·마무리까지 (구체 설계도 v1, 2026-06-17)

**대상**: 개발자 로컬 Windows + RTX 4070. **목표**: corpus_ko 데이터로 loop-C 실학습 1라운드를 돌려 **ΔW(승률 변화)**를 얻고, 그 결과로 나머지(DPO 본학습→생성품질→T2/T3/T4)를 진행·마무리.

## 0. 디렉토리 배치 (두 위치를 연결하는 게 핵심)
```
[A] 레포(코드+킷+패키지)   :  C:\dev\literary-os            ← git clone
        └ run_first_training.py 킷  : docs\sessions\2026-06-16_first_training_kit\
        └ literary_system\          : pip install -e . 대상
[B] 데이터(비커밋, 로컬전용):  C:\Users\inyoung pharm\Documents\Claude\Projects\literary\corpus_ko
        ├ scenes\          (455작품 실명작 씬 — 선호쌍 ref 원천)
        ├ emb_cache\       (313 임베딩 샤드 — RAG용)
        └ experiments\loop_c_dpo.py , dpo_pairs.jsonl(현재 17쌍)
```
→ **선호쌍은 [B]에서 생성, 학습은 [A]의 킷이 [B]의 dpo_pairs.jsonl을 가리켜 실행.**

## 1. 데이터 흐름 설계도 (전 과정)
```
[B] corpus_ko\scenes (455) + OpenAI(gen+panel)
   └─① loop_c_dpo.py ─────────────►  [B] experiments\dpo_pairs.jsonl
                                        (선호쌍 {func,genre,ref_id,winner,draft,ref}, verbatim=로컬전용)
                                              │
[A] run_first_training.py + 4070 QLoRA DPO ──②──► [B] lora_out\  (LoRA 어댑터)  +  콘솔: W0→W1
                                              │
                                        ③ 수용 게이트 G_LOOPC_WINRATE
                                          ΔW=W1−W0>0  AND  KL≤τ  AND  구조게이트 비퇴행
                                              ├─ PASS → 어댑터 채택(버전 보관) → 라운드++(①로, 선호쌍 확대)
                                              └─ FAIL → 어댑터 폐기 → 선호쌍 확대·하이퍼 조정 후 재시도
                                              │
                                   ④ ΔW 정량화 → DPO 본학습(선호쌍 수백·다라운드·KL)
                                      → 생성 vs 실명작 승률↑ → T2 NextEpisodeBench(전편 평가)
                                      → T3 생성본체 7-pass 실구현 → T4/E.3 작가 UI·개입
```

## 2. 설치 (한 번만)
```powershell
# [A] 레포·패키지
git clone https://github.com/limsanghyuk/literary-os.git C:\dev\literary-os
cd C:\dev\literary-os
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -e .
# GPU/학습 의존
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install transformers datasets peft trl accelerate bitsandbytes
# 상류(선호쌍 생성)용 — OpenAI
pip install openai            # 또는 표준 urllib만 쓰면 불필요
```
모델 인증(택1): 게이트 Llama → `huggingface-cli login`(라이선스 동의 후) / 비게이트 → `--base Qwen/Qwen2.5-3B-Instruct`.
(상세: 같은 폴더 `MODEL_INSTALL_AND_RUN.md`)

## 3. ① 선호쌍 생성·확대 (corpus_ko에서, OpenAI 필요)
`loop_c_dpo.py`는 `scenes/`의 실명작 씬을 ref로, 생성 draft를 만들어 3페르소나 패널이 승자 판정 → `dpo_pairs.jsonl`에 append(재실행=누적).
```powershell
cd "C:\Users\inyoung pharm\Documents\Claude\Projects\literary\corpus_ko"
$env:OPENAI_API_KEY="sk-..."          # 본인 키
# ※ 스크립트가 /tmp/oai.key를 읽게 돼 있으면 1줄만 수정:
#    KEY=open("/tmp/oai.key").read().strip()  →  KEY=os.environ["OPENAI_API_KEY"]
python experiments\loop_c_dpo.py      # 재실행할수록 쌍 누적(현재 17 → 수백 목표)
```
**산출물**: `experiments\dpo_pairs.jsonl`(쌍 수 = 콘솔에 출력). ※verbatim 포함 → **로컬 전용, 허브 커밋 금지**(허브엔 쌍 수·승률만).

## 4. ② 킷 학습 (4070, 레포에서 [B]를 가리켜)
```powershell
cd C:\dev\literary-os\docs\sessions\2026-06-16_first_training_kit
# 스모크(환경 점검)
python run_first_training.py --pairs sample_dpo_smoke.jsonl --smoke --base Qwen/Qwen2.5-3B-Instruct
# 실데이터 학습 (corpus_ko의 선호쌍을 절대경로로 지정)
python run_first_training.py `
  --pairs "C:\Users\inyoung pharm\Documents\Claude\Projects\literary\corpus_ko\experiments\dpo_pairs.jsonl" `
  --base meta-llama/Llama-3.2-3B `
  --out  "C:\Users\inyoung pharm\Documents\Claude\Projects\literary\corpus_ko\lora_out"
```
**산출물**: `corpus_ko\lora_out\`(LoRA 어댑터) + 콘솔 **baseline W0(0.588) → 학습후 W1** + 학습 로그.

## 5. ③ 산출물 처리 (수용 게이트)
| 산출물 | 위치 | 처리 방식 |
|---|---|---|
| `dpo_pairs.jsonl` | corpus_ko\experiments\ | **로컬 보관·누적**(verbatim). 허브엔 집계(쌍 수·draft승률)만 리포트 |
| `lora_out\` (어댑터) | corpus_ko\lora_out\ | **ΔW=W1−W0>0이면 채택**(버전 폴더로 보관: `lora_out\round1\`) / ≤0이면 삭제 |
| W0·W1·ΔW | 콘솔/로그 | **수치만 허브 리포트**(`docs/sessions/.../roundN_result.md`, verbatim 없음) |

수용 판정(loop-C 폐회로 G_LOOPC_WINRATE, V774): **ΔW>0 AND KL 가드 통과 AND 구조게이트(LOSConstitution R) 비퇴행** → 채택. 단일 라운드·소수쌍은 노이즈 → 최소 N라운드 이동평균/표본 확대로 신뢰.

## 6. ④ 이후 "나머지 진행·마무리" (무엇이 끝나는가)
1. **ΔW 정량화**: W0=0.588 대비 움직임 측정 = loop-C 격차의 첫 수치(메커니즘 작동 증명).
2. **DPO 본학습**: 선호쌍 17→수백 확대(3번 반복) + 여러 라운드 + KL 가드 → 생성 vs 실명작 승률을 단계적 상향.
3. 승률이 **측정상 명작 수준에 근접**하면 → **T2 NextEpisodeBench**(N화→N+1화 전편 평가)로 전편 품질 검증 → **T3 생성본체 7-pass 실구현**(설계도 `2026-06-17_t3_7pass_io_contract_v1.md`) → **T4/E.3 작가 UI·개입**(2단계).
- 즉 **T1(이 런북)이 "자율 생성 품질이 실제로 오르는가"를 수치로 증명**하면, 그 위에 전편 평가·생성본체·UI가 순차로 얹혀 1단계(자율 인간팀급 생성)가 마무리됨.

## 7. 정직한 전제·주의
- ①은 **OpenAI 비용**(생성+판정 LLM 호출) 발생. ②는 4070 전기·시간만(로컬 $0).
- `loop_c_dpo.py`의 키 경로(`/tmp/oai.key`)는 Windows에서 **env 읽기로 1줄 수정** 필요(위 §3).
- verbatim(draft/ref 원문)은 **절대 허브 커밋 금지** — 라운드 결과는 수치·집계만.
- 17쌍·1회는 "움직이는가"만. 품질 향상은 데이터 확대+반복이 본론.
```
```
