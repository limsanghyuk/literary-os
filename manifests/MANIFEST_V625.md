# MANIFEST V625

**버전**: v10.30.0  
**날짜**: 2026-05-25  
**Gates**: 60/60 PASS  
**Tests**: 6,980

## 신규 파일

| 파일 | 유형 |
|---|---|
| `.github/workflows/biweekly_train.yml` | CI 워크플로우 |
| `tools/check_runpod_availability.py` | 신규 |
| `tools/notify_slack.py` | 신규 |
| `tests/unit/test_v625_auto_recovery.py` | 신규 (+50 TC) |
| `docs/adr/ADR-092.md` | 신규 |
| `docs/changelog/CHANGELOG_V625.md` | 신규 |
| `manifests/MANIFEST_V625.md` | 신규 |

## 수정 파일

| 파일 | 변경 내용 |
|---|---|
| `literary_system/finetune/lora_job_runner.py` | AutoRecoveryScheduler + CLI 추가 |
| `literary_system/gates/release_gate.py` | version "V625" |
| `pyproject.toml` | 10.29.0 → 10.30.0 |
| `tools/test_inventory.json` | 6,980 TC |
