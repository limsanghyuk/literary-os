# Literary-OS 모델 설치 · RTX 4070 연결 · 실측–학습 설계 (2026-06-19)

기준 v13.40.0. 설계도 docx: C:\claude\Literary-OS_모델설치_4070연결_실측학습_설계도.docx

## 1. "우리 모델" = 2계층
- ① **literary-os 코어(LLM-0)**: 공식·critic·NKG·loop-C·corpus = 판단/평가/기획 두뇌. **로컬 CPU**(GPU 불요), pip install -e .
- ② **생성기 LM**: 산문 쓰는 오픈소스 LM(3B/8B). loop-C로 미세조정 대상. **4070 GPU**, HF 다운로드.
→ 두뇌=소유 코드, 손=오픈소스 LM을 우리 데이터로 길들임. 4070은 ②만.

## 2. 설치 (4단계, 기존 MODEL_INSTALL_AND_RUN_v1 정본)
① 레포+코어: `git clone` → `pip install -e .` / ② GPU: torch(cu121)·trl·peft·bitsandbytes / ③ 생성기 LM: 첫 실행시 HF 자동다운로드(비게이트 Qwen 즉시 / 게이트 Llama는 login) / ④ 스모크: `run_first_training.py --smoke`.

## 3. 4070 연결(이미 구현 V767)
LocalPreflight(점검)→LocalGPUAdapter(QLoRA 4bit·VRAM 12GB 가드)→train_4070.py(DPOTrainer)→ProviderRouter(LOCAL). VRAM: 3B≈6GB·7B≈8GB·8B≈11.5GB(빠듯)·13B+ 폴백.

## 4. 실측→반영→학습 루프(V774·782~787)
①생성(7-pass+생성기) →②실측(M1 자격·M2 NextEp 쌍대·M3 분포가드) →③반영(loop-C 선호쌍) →④학습(4070 QLoRA DPO) →⑤ΔW(W0→W1) →⑥수용판정(G_LOOPC_WINRATE) →⑦반복. 베이스라인 생성 46% vs 명작 54%, 목표=46%↑. 천장=모작(독창성은 인간 최종시험).

## 5. 오픈소스 LM 검토(4070 12GB·한국어·상업)
| 모델 | 한국어 | 라이선스 | 권고 |
|---|---|---|---|
| **Qwen2.5-3B-Instruct** | 우수 | Apache2.0(상업OK) | ★출발(비게이트·즉시·반복빠름) |
| **Qwen2.5-7B-Instruct** | 우수 | Apache2.0(상업OK) | ★★품질(QLoRA≈8GB fit) |
| EXAONE-3.5-7.8B | 최상(한국특화) | 비상업(EXAONE License) | 연구·실험만(제품 부적합) |
| Llama-3.2-3B / 3.1-8B | 양호 | 커뮤니티(상업OK*) | 게이트(동의+토큰), 대안 |
| Gemma-2-9B | 양호 | Gemma | 12GB 경계, 비권장 |

**권고**: Qwen2.5-3B(출발)→Qwen2.5-7B(품질). 둘 다 Apache2.0=상업 안전. EXAONE은 한국어 최상이나 비상업이라 제품 가중치 부적합(연구만).

## 6. 준비 상태
설치·연결·루프·게이트 전부 코드 완비. 남은 건 이 설계대로 4070 1라운드 실행. 클라우드 대체=RunPod GPU 키 시 CloudTrainingNode 동일 루프.
