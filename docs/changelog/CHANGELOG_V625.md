# CHANGELOG V625 — v10.30.0

**날짜**: 2026-05-25  
**커밋**: (V625)  
**이전 버전**: v10.29.0 (V624)

## 신규 기능

### biweekly_train CI 워크플로우
- `.github/workflows/biweekly_train.yml`: 격주 LoRA+RLHF 자동 훈련 (ADR-092)
- 매월 1·15일 02:00 KST 자동 실행 + workflow_dispatch
- 3-Job 구조: check-runpod → train → post-train-gate

### RunPod 가용성 체커
- `tools/check_runpod_availability.py`: RunPodChecker 클래스
- GPU 타입별 가용성 확인 + 폴백 목록

### Slack 알림
- `tools/notify_slack.py`: SlackNotifier 클래스
- info/warn/error 레벨, #losdb-ops 기본 채널

### Lambda 폴백 + 자동 복구
- `literary_system/finetune/lora_job_runner.py` 확장
  - `AutoRecoveryScheduler`: 백엔드 자동 선택 + 에스컬레이션 판단
  - CLI 진입점: `--backend runpod|lambda_h100|auto`

## 테스트

- `tests/unit/test_v625_auto_recovery.py`: +50 TC (TC-01~TC-50)
  - TC-01~10: RunPodChecker 단위
  - TC-11~20: SlackNotifier 단위
  - TC-21~30: AutoRecoveryScheduler 단위
  - TC-31~40: tools CLI smoke
  - TC-41~50: biweekly_train 통합

## 지표

| 항목 | 값 |
|---|---|
| 버전 | v10.30.0 |
| Gates | 60/60 PASS |
| Tests | 6,980 (+50) |
| 신규 파일 | 4종 |
| ADR | ADR-092 |
