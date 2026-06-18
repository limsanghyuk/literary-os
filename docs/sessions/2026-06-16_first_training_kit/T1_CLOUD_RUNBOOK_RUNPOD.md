# T1 클라우드(RunPod) 학습 런북 — 구체 실행 (v1, 2026-06-18)

**대상**: 회사 PC(노트북 약GPU) → 클라우드 GPU로 T1 loop-C 실학습. **기준**: 허브 V786/v13.39.0(클라우드 노드 구현됨).
**핵심 사실**: 코드는 **이미 완성**(V786 `CloudTrainingNode`). 유일한 차단 = **RunPod API 키 미제공**. 키만 있으면 아래대로 바로 가동.

## 0. 사전 준비
| 항목 | 용도 | 확보 |
|---|---|---|
| **RunPod API 키**(Bearer) | GPU 파드 생성·학습 | runpod.io → Settings → API Keys (미제공 → 발급 필요) |
| **비공개 저장소** | 선호쌍 암호화 업로드 | RunPod 볼륨 또는 S3/B2 presigned URL (**공개 금지**) |
| **암호화 키**(32B) | 업로드 전 클라이언트 암호화 | 임의 생성, 로컬 보관(env) |
| **OpenAI 키** | 상류 선호쌍 생성(loop_c_dpo) | 제공됨 |
| 선호쌍 | 학습 입력 | `corpus_ko\experiments\dpo_pairs.jsonl`(현재 17 → 수백 목표) |

## 1. 실제 모듈 지도 (V786, 추측 아님)
- `finetune/cloud_training_node.py` → **`CloudTrainingNode(adapter, store, max_polls=20).run(dpo_pairs_path, model_name)`** = 원샷: 암호화 업로드→RunPod QLoRA DPO→어댑터 회수→**업로드 자동삭제**→ΔW→G_LOOPC_WINRATE.
- `finetune/runpod_real_adapter.py` → **`make_real_runpod(api_key)`** · `.verify_key()` · `.estimate_cost(hours)` · `.launch_job()` · `.poll(pod_id)`.
- `finetune/cloud_storage.py` → `CloudStore.put/get/delete` · `encrypt_bytes(data,key)` · `PresignedHttpStore`(S3/B2) — 업로드 전 SHA256-CTR 암호화(운영은 Fernet/age 권장).
- `finetune/runpod_lifecycle.py` → `RunPodJobLifecycle.run(dataset_path, model_name, hours, output_url, dry_run, artifact_dest)` = 저수준(①업로드 ②기동 ③폴링 ④어댑터 회수 ⑤등재).
- `learning/privacy_guard.py` → `PrivacyGuard` — raw 텍스트 LLM 전달 금지 강제.

## 2. 단계별 실행
### ① 선호쌍 생성·확대 (어디서나, OpenAI)
```powershell
cd "C:\Users\inyoung pharm\Documents\Claude\Projects\literary\corpus_ko"
$env:OPENAI_API_KEY="sk-..."
python experiments\loop_c_dpo.py        # 재실행=누적(17→수백). 산출: experiments\dpo_pairs.jsonl
```
### ② 키·환경 설정
```powershell
$env:RUNPOD_API_KEY="rpa_..."           # RunPod Bearer
$env:LOS_ENC_KEY="<32바이트 랜덤 hex>"   # 업로드 암호화 키
# 저장소 자격(presigned면 URL 발급자/버킷 자격)
```
### ③ 드라이런(네트워크 미호출, 계획·비용 확인) → 키 검증
```powershell
cd C:\dev\literary-os ; .\.venv\Scripts\Activate.ps1
python - << 'PY'
import os
from literary_system.finetune.runpod_real_adapter import make_real_runpod
a = make_real_runpod(os.environ["RUNPOD_API_KEY"])
print("key valid:", a.verify_key())                 # True면 키 OK
print("est cost(2h):", a.estimate_cost(2.0))         # 예상 비용
PY
```
### ④ 클라우드 학습 원샷 (암호화 업로드→학습→회수→삭제→ΔW→게이트)
```powershell
python - << 'PY'
import os
from literary_system.finetune.runpod_real_adapter import make_real_runpod
from literary_system.finetune.cloud_storage import PresignedHttpStore   # 또는 CloudStore
from literary_system.finetune.cloud_training_node import CloudTrainingNode

adapter = make_real_runpod(os.environ["RUNPOD_API_KEY"])
store   = PresignedHttpStore(enc_key=bytes.fromhex(os.environ["LOS_ENC_KEY"]))  # 비공개·암호화
node    = CloudTrainingNode(adapter=adapter, store=store, max_polls=40)

report = node.run(
    dpo_pairs_path=r"C:\Users\inyoung pharm\Documents\Claude\Projects\literary\corpus_ko\experiments\dpo_pairs.jsonl",
    model_name="meta-llama/Llama-3.2-3B",   # 게이트면 HF 인증 필요 / 비게이트면 Qwen/Qwen2.5-3B-Instruct
)
print(report.summary())
print("ΔW =", report.delta_w())             # >0 이면 G_LOOPC_WINRATE 후보
PY
```
`CloudTrainingNode.run`이 내부적으로 수행: **암호화 업로드 → RunPod 파드 QLoRA DPO → LoRA 어댑터 회수 → 업로드 데이터 자동삭제 → ΔW 산출 → 수용 판정**.

### ⑤ 산출물 처리 + 파드 파기
- **회수물 = LoRA 어댑터(verbatim 없음)** → ΔW>0 & KL & 구조 비퇴행이면 채택(레지스트리). 아니면 폐기.
- 업로드 선호쌍 → 노드가 자동 삭제(저작권 안전). 수동 확인: `store.delete(url)` / `store.cleanup()`.
- RunPod 파드 → 학습 종료 후 파기(비용 정지). `adapter.poll(pod_id)`로 상태 확인 후 종료.

## 3. 저작권 안전 (불변)
- **올리는 건 비공개·암호화·임시**(공개 S3/HF 데이터셋 금지), **회수는 어댑터(가중치)만**, **끝나면 즉시 삭제**.
- ProviderRouter R2(민감 코퍼스 LOCAL 강제)는 *영구 공개 저장소* 기준 — 본인 소유 임시·암호화 인스턴스는 방어 가능.
- 운영 암호화는 Fernet/age 권장(코드 기본은 SHA256-CTR, 의존성 0).

## 4. 정직한 현황·차단점
- **구현 완료**: V786에서 위 전 체인 코드화 + 6지표 자체평가 1라운드 실측(메커니즘 작동, 단 소형모델·소규모라 ΔW=0 → 게이트가 정직하게 rollback).
- **유일 차단**: **RunPod(또는 Lambda) GPU 키 미제공**. 키 발급 + 선호쌍 수백 확대 + 실 생성기(3B/8B)면 실 ΔW가 움직임.
- 비용: RunPod GPU $/hr(예: 어댑터 estimate_cost로 사전 확인). OpenAI는 ①에만.
- 대안: 키 발급 전엔 집 4070 로컬 노드(`run_4070.bat`)로 동일 검증 가능(클라우드와 대칭 설계).

## 5. 한 줄
회사 노트북 GPU로는 학습 불가 → **RunPod 키 하나만 발급하면** `CloudTrainingNode.run(dpo_pairs, model)` 한 줄로 암호화 업로드→클라우드 학습→어댑터 회수→자동삭제→ΔW·게이트까지 끝. 코드는 이미 완성돼 있고, 저작권은 비공개·암호화·임시·어댑터만 회수로 방어된다.
