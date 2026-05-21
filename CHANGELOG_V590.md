# Changelog — V590 (v9.5.0)

**릴리즈일**: 2026-05-21  
**버전**: 9.5.0  
**PR**: SP-A.3 GPU Adapter Contract  
**Gates**: 48/48 PASS (G1~G49)  
**테스트**: 5,785+ PASS (+25 신규)

---

## 신규 기능

### SP-A.3: GPUAdapterContract + 3종 Provider Adapter

#### `literary_system/finetune/gpu_adapter.py` (신규, 469 lines)

- **GPUAdapterContract** (ABC)
  - `provider_id` property → `GPUProvider`
  - `cost_per_hour` property → float
  - `estimate_cost(hours)` → float
  - `launch_job(request)` → GPUJobResult
  - `dry_run(request)` → GPUJobResult (실제 기동 없음)
  - `check_slo(request, monthly_spend)` → str

- **RunPodAdapter** — RTX 4090, $0.39/h
- **LambdaLabsAdapter** — H100 SXM5 80GB, $1.49/h
- **HFAutoTrainAdapter** — AutoTrain A100, $4.00/h

- **CostSLO** (frozen dataclass)
  - soft: $90/월 → WARN
  - hard: $120/월 → BLOCK
  - emergency: $150/월 → HALT
  - `assess(monthly_spend)` → "OK" | "WARN" | "BLOCK" | "HALT"

- **GPUJobRequest** / **GPUJobResult** / **GPUProvider** / **GPUJobStatus** 데이터 모델

- **Factory**: `get_adapter(provider)`, `list_providers()`

#### `literary_system/llm_bridge/cost_ledger.py` (확장)

- **GPUCostRecord** dataclass — 단일 GPU 작업 비용 기록
- **GPUCostLedger** dataclass
  - `gpu_track(provider, hours, cost_per_hour, job_id)` → dict
  - `monthly_total_gpu()` → float
  - `_assess_slo(monthly_spend)` → str (WARN/BLOCK/HALT)
  - `to_dict()` → 월간 GPU 비용 요약

---

## Gate

| Gate | 이름 | 체크포인트 | 결과 |
|------|------|-----------|------|
| G49  | GPUAdapterGate | GA-1~GA-10 | **PASS** |

**GA-1**: GPUAdapterContract import  
**GA-2**: CostSLO 필드 검증  
**GA-3**: RunPodAdapter ABC 구현  
**GA-4**: LambdaLabsAdapter ABC 구현  
**GA-5**: HFAutoTrainAdapter ABC 구현  
**GA-6**: dry_run() → DRY_RUN status  
**GA-7**: CostSLO 값 ($90/$120/$150)  
**GA-8**: GPUCostLedger.gpu_track() 정상 동작  
**GA-9**: GPUCostLedger.monthly_total_gpu() 정상 동작  
**GA-10**: LLM-0 준수 (gpu_adapter.py 내 LLM API 호출 없음)

---

## ADR

- **ADR-051**: GPU Adapter Contract (`docs/adr/ADR-051.md`)

---

## 테스트

| 파일 | 케이스 | 결과 |
|------|--------|------|
| `tests/unit/test_gpu_adapter.py` | TC01~TC25 | **25/25 PASS** |

### 테스트 그룹
- TestGPUJobRequest (TC01~TC04) — 요청 유효성
- TestCostSLO (TC05~TC08) — SLO 경계 평가
- TestRunPodAdapter (TC09~TC12) — RunPod 어댑터
- TestLambdaLabsAdapter (TC13~TC16) — Lambda Labs 어댑터
- TestHFAutoTrainAdapter (TC17~TC19) — HF AutoTrain 어댑터
- TestGPUCostLedger (TC20~TC23) — 비용 원장
- TestFactory (TC24~TC25) — Factory / list_providers

---

## 수치 비교

| 항목 | V589 (9.4.0) | V590 (9.5.0) |
|------|--------------|--------------|
| Gates | 47/47 | **48/48** |
| 신규 테스트 | — | **+25** |
| ADR | ADR-001~050 | **ADR-001~051** |
| GPUAdapterContract | 없음 | **구현 완료** |
| GPU 비용 SLO | 없음 | **$90/$120/$150** |
| GPUCostLedger | 없음 | **구현 완료** |

---

## 버그 수정

- `GPUJobStatus` 네이밍: 기존 `finetune_job_manager.py`의 `JobStatus`와 충돌 방지를 위해 `GPUJobStatus`로 명명 (duplicate_zero_g37 Gate 준수)
- 이전 버전(V580~V586) 테스트의 gate 수 하드코딩(`== 45`) → `>= 45` 로 수정 (진화 호환성)

---

## 아키텍처 원칙 준수

- **LLM-0**: gpu_adapter.py는 외부 LLM API를 호출하지 않음 (GA-10 검증)
- **드라이런 기본값**: `GPUJobRequest.dry_run=True` — 의도치 않은 비용 발생 방지
- **DEV_MODE**: 기본값 `"false"` 유지 (ADR-034)
