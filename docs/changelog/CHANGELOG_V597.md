# Changelog — V597 (v10.2.0)

**날짜**: 2026-05-21  
**Phase**: Phase B SP-B.1 — LoRA Fine-tuning Pipeline  
**Commit**: (HEAD)  
**이전 버전**: v10.1.0 (V596)

---

## 신규 파일 (5개)

### literary_system/finetune/lora_training_config.py
- `LoRATrainingConfig` dataclass — 본안 B-M-05 구현
  - rank=16, alpha=32, target_modules=[q/k/v/o_proj], bf16=True
  - `LoRAScheduleType`: FULL_BIWEEKLY / FINE_WEEKLY / MANUAL
  - `LoRAQuantizationType`: NONE / INT8 / INT4 / NF4
  - 팩토리: `default_full()`, `default_fine()`, `exaone_candidate()`
  - `to_dict()` / `from_dict()` 라운드트립 직렬화

### literary_system/finetune/lora_job_runner.py
- `LoRAJobRunner` — GPUAdapterContract (V590) 연동 학습 실행기
  - `BiweeklyScheduler` — 격주/주간 due 판단 (본안 B-M-06)
  - `JobRunRecord` dataclass — JSONL 영속화
  - SLO 집행: HALT(≥$150)→RuntimeError, BLOCK(≥$120)→RuntimeError, WARN(≥$90)→Warning
  - `monthly_spend()`, `slo_status()`, `next_due()`, `history()`

### deploy/helm/train_plane/ (본안 보강 B-M-16)
- `Chart.yaml` — literary-os-train-plane v0.1.0
- `values.yaml` — GPU 리소스, CostSLO, 스케줄 설정
- `templates/lora-job.yaml` — LoRA 학습 Job 템플릿
- `templates/cronjob.yaml` — 격주/주간 CronJob (literary-train 네임스페이스)
- `README.md` — TrainPlane 설치 가이드

### docs/adr/ADR-057.md
- LoRA 하이퍼파라미터 정책 (rank=16, B-M-05)
- TrainPlane/ServePlane 격리 정책 (B-M-16)
- 월 SLO $96 정책 (B-M-06)

### tests/unit/test_v597_lora_training.py
- TC-A1~A3: LoRATrainingConfig 검증 / 라운드트립
- TC-B1~B4: LoRAJobRunner dry_run / 영속화 / SLO BLOCK / monthly_spend
- TC-C1~C2: BiweeklyScheduler 경계값 / 우선순위

---

## 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `literary_system/finetune/__init__.py` | LoRATrainingConfig, LoRAJobRunner, BiweeklyScheduler 심볼 export |
| `docs/adr/INDEX.md` | ADR-057 항목 추가 |
| `pyproject.toml` | version 10.1.0 → 10.2.0 |
| `README.md` | version badge 10.2.0, tests 6211 PASS |
| `RELEASE_INFO.txt` | V597 / v10.2.0 / 6211 PASS |
| `tools/test_inventory.json` | test_count=6211, source_hash=5758db54027db8b8 |

---

## 테스트 수치

| 항목 | V596 | V597 |
|------|------|------|
| 총 테스트 | 6,202 | **6,211** |
| 신규 TC | — | +9 |
| Release Gate | 51/51 | **51/51** |
| preflight step13 | PASS | PASS |
| preflight step14 | PASS | PASS |
| preflight step15 | PASS | PASS |

---

## 본안 보강 이행 현황 (SP-B.1)

| 보강 ID | 내용 | 완료 V |
|---------|------|--------|
| B-M-01 | sha256 chain ProvenanceLedger | V596 ✅ |
| B-M-02 | DatasetRegistry + DVC remote | V596 ✅ |
| B-M-04 | Llama-3.1-8B + EXAONE A/B | V597 ✅ |
| B-M-05 | rank=16, q/k/v/o_proj | V597 ✅ |
| B-M-06 | 격주 학습 + 주간 미세조정 월$96 | V597 ✅ |
| B-M-12 | DSR 30일 SLA | V596 ✅ |
| B-M-16 | TrainPlane Helm 격리 | V597 ✅ |
