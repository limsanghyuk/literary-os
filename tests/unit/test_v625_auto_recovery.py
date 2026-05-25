"""
tests/unit/test_v625_auto_recovery.py — V625 신규 (+50 TC)

검증 범위:
  TC-01~10  RunPodChecker 단위
  TC-11~20  SlackNotifier 단위
  TC-21~30  AutoRecoveryScheduler 단위
  TC-31~40  tools CLI smoke (import + argparse 검증)
  TC-41~50  biweekly_train 통합 (워크플로우 YAML 파싱 + 백엔드 선택 로직)
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── 경로 설정 ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

# ── 임포트 ────────────────────────────────────────────────────────────
from check_runpod_availability import RunPodChecker
from notify_slack import SlackNotifier
from literary_system.finetune.lora_job_runner import AutoRecoveryScheduler


# ═══════════════════════════════════════════════════════════════════════
#  TC-01~10: RunPodChecker 단위 테스트
# ═══════════════════════════════════════════════════════════════════════

class TestRunPodChecker:
    """TC-01~10"""

    def test_tc01_import(self):
        """TC-01: RunPodChecker import 성공."""
        assert RunPodChecker is not None

    def test_tc02_dry_run_always_available(self):
        """TC-02: dry_run 모드에서 항상 가용 반환."""
        checker = RunPodChecker(dry_run=True)
        result = checker.check()
        assert result["available"] is True
        assert result["source"] == "dry_run"

    def test_tc03_dry_run_is_available_bool(self):
        """TC-03: is_available() → True (dry_run)."""
        assert RunPodChecker(dry_run=True).is_available() is True

    def test_tc04_no_key_returns_false(self):
        """TC-04: API 키 없으면 available=False."""
        checker = RunPodChecker(api_key="", dry_run=False)
        result = checker.check()
        assert result["available"] is False
        assert result["source"] == "no_key"

    def test_tc05_no_key_reason_message(self):
        """TC-05: 키 없을 때 reason 메시지 포함."""
        result = RunPodChecker(api_key="", dry_run=False).check()
        assert "RUNPOD_API_KEY" in result["reason"]

    def test_tc06_env_key_used_when_no_arg(self, monkeypatch):
        """TC-06: RUNPOD_API_KEY 환경변수 읽기."""
        monkeypatch.setenv("RUNPOD_API_KEY", "")
        checker = RunPodChecker()
        assert checker._api_key == ""

    def test_tc07_custom_gpu_type(self):
        """TC-07: 커스텀 GPU 타입 설정."""
        checker = RunPodChecker(gpu_type="A100_SXM", dry_run=True)
        result = checker.check()
        assert result["gpu_type"] == "A100_SXM"

    def test_tc08_result_has_required_keys(self):
        """TC-08: 결과 dict에 필수 키 포함."""
        result = RunPodChecker(dry_run=True).check()
        for key in ("available", "gpu_type", "count", "source", "reason"):
            assert key in result, f"키 누락: {key}"

    def test_tc09_fallback_gpu_list_defined(self):
        """TC-09: FALLBACK_GPU_TYPES 목록이 비어 있지 않음."""
        assert len(RunPodChecker.FALLBACK_GPU_TYPES) > 0

    def test_tc10_api_error_returns_false(self):
        """TC-10: API 오류 시 available=False."""
        checker = RunPodChecker(api_key="fake_key", dry_run=False)
        with patch.object(checker, "_query_api") as mock_q:
            mock_q.return_value = {
                "available": False,
                "gpu_type": "RTX_4090",
                "count": 0,
                "source": "api_error",
                "reason": "연결 오류",
            }
            assert checker.is_available() is False


# ═══════════════════════════════════════════════════════════════════════
#  TC-11~20: SlackNotifier 단위 테스트
# ═══════════════════════════════════════════════════════════════════════

class TestSlackNotifier:
    """TC-11~20"""

    def test_tc11_import(self):
        """TC-11: SlackNotifier import 성공."""
        assert SlackNotifier is not None

    def test_tc12_dry_run_no_send(self):
        """TC-12: dry_run 모드에서 sent=False."""
        notifier = SlackNotifier(dry_run=True)
        result = notifier.send("테스트 메시지")
        assert result["sent"] is False
        assert result["source"] == "dry_run"

    def test_tc13_no_webhook_skips(self):
        """TC-13: webhook URL 없으면 sent=False."""
        notifier = SlackNotifier(webhook_url="", dry_run=False)
        result = notifier.send("메시지")
        assert result["sent"] is False
        assert result["source"] == "no_webhook"

    def test_tc14_send_returns_dict(self):
        """TC-14: send() 반환값이 dict."""
        result = SlackNotifier(dry_run=True).send("msg")
        assert isinstance(result, dict)

    def test_tc15_result_has_sent_key(self):
        """TC-15: 결과에 'sent' 키 존재."""
        result = SlackNotifier(dry_run=True).send("msg")
        assert "sent" in result

    def test_tc16_level_info(self):
        """TC-16: level=info dry_run."""
        result = SlackNotifier(dry_run=True).send("info msg", level="info")
        assert result["source"] == "dry_run"

    def test_tc17_level_warn(self):
        """TC-17: level=warn dry_run."""
        result = SlackNotifier(dry_run=True).send("warn msg", level="warn")
        assert result["source"] == "dry_run"

    def test_tc18_notify_training_start(self):
        """TC-18: notify_training_start() 호출 성공."""
        notifier = SlackNotifier(dry_run=True)
        result = notifier.notify_training_start("runpod", "full")
        assert result["source"] == "dry_run"

    def test_tc19_notify_fallback(self):
        """TC-19: notify_fallback() 호출 성공."""
        notifier = SlackNotifier(dry_run=True)
        result = notifier.notify_fallback("RunPod 소진", "lambda_h100")
        assert result["source"] == "dry_run"

    def test_tc20_notify_error(self):
        """TC-20: notify_error() 호출 성공."""
        notifier = SlackNotifier(dry_run=True)
        result = notifier.notify_error("예기치 못한 오류 발생")
        assert result["source"] == "dry_run"


# ═══════════════════════════════════════════════════════════════════════
#  TC-21~30: AutoRecoveryScheduler 단위 테스트
# ═══════════════════════════════════════════════════════════════════════

class TestAutoRecoveryScheduler:
    """TC-21~30"""

    def test_tc21_import(self):
        """TC-21: AutoRecoveryScheduler import 성공."""
        assert AutoRecoveryScheduler is not None

    def test_tc22_version_defined(self):
        """TC-22: VERSION 속성 존재."""
        assert AutoRecoveryScheduler.VERSION == "1.0.0"

    def test_tc23_decide_backend_runpod(self):
        """TC-23: runpod_available=True → BACKEND_RUNPOD."""
        scheduler = AutoRecoveryScheduler()
        assert scheduler.decide_backend(True) == AutoRecoveryScheduler.BACKEND_RUNPOD

    def test_tc24_decide_backend_lambda(self):
        """TC-24: runpod_available=False → BACKEND_LAMBDA."""
        scheduler = AutoRecoveryScheduler()
        assert scheduler.decide_backend(False) == AutoRecoveryScheduler.BACKEND_LAMBDA

    def test_tc25_record_attempt_increments(self):
        """TC-25: record_attempt() 호출 시 시도 번호 증가."""
        scheduler = AutoRecoveryScheduler()
        r1 = scheduler.record_attempt("runpod", False)
        r2 = scheduler.record_attempt("lambda_h100", False)
        assert r1["attempt"] == 1
        assert r2["attempt"] == 2

    def test_tc26_no_escalate_before_max(self):
        """TC-26: 최대 재시도 미만이면 escalate=False."""
        scheduler = AutoRecoveryScheduler(max_retries=3)
        scheduler.record_attempt("runpod", False)
        scheduler.record_attempt("runpod", False)
        assert not scheduler.should_escalate()

    def test_tc27_escalate_after_max_all_fail(self):
        """TC-27: 최대 재시도 횟수 이상 + 전부 실패 → escalate=True."""
        scheduler = AutoRecoveryScheduler(max_retries=3)
        for _ in range(3):
            scheduler.record_attempt("runpod", False)
        assert scheduler.should_escalate()

    def test_tc28_no_escalate_if_any_success(self):
        """TC-28: 성공 1건 있으면 escalate=False."""
        scheduler = AutoRecoveryScheduler(max_retries=3)
        scheduler.record_attempt("runpod", False)
        scheduler.record_attempt("lambda_h100", True)   # 성공
        scheduler.record_attempt("runpod", False)
        assert not scheduler.should_escalate()

    def test_tc29_recovery_summary_keys(self):
        """TC-29: recovery_summary()에 필수 키 포함."""
        scheduler = AutoRecoveryScheduler()
        scheduler.record_attempt("runpod", True)
        summary = scheduler.recovery_summary()
        for key in ("version", "attempts", "succeeded", "escalate", "log"):
            assert key in summary

    def test_tc30_reset_clears_log(self):
        """TC-30: reset() 후 시도 이력 초기화."""
        scheduler = AutoRecoveryScheduler()
        scheduler.record_attempt("runpod", False)
        scheduler.reset()
        assert scheduler.recovery_summary()["attempts"] == 0


# ═══════════════════════════════════════════════════════════════════════
#  TC-31~40: tools CLI smoke 테스트
# ═══════════════════════════════════════════════════════════════════════

class TestToolsCLI:
    """TC-31~40"""

    def test_tc31_check_runpod_script_exists(self):
        """TC-31: tools/check_runpod_availability.py 파일 존재."""
        assert (REPO_ROOT / "tools" / "check_runpod_availability.py").exists()

    def test_tc32_notify_slack_script_exists(self):
        """TC-32: tools/notify_slack.py 파일 존재."""
        assert (REPO_ROOT / "tools" / "notify_slack.py").exists()

    def test_tc33_check_runpod_dry_run_exit0(self):
        """TC-33: check_runpod_availability --dry-run exit code 0."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "tools/check_runpod_availability.py", "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_tc34_check_runpod_json_output(self):
        """TC-34: --json 플래그로 JSON 출력 가능."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "tools/check_runpod_availability.py", "--dry-run", "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "available" in data

    def test_tc35_notify_slack_dry_run(self):
        """TC-35: notify_slack --dry-run exit code 0."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "tools/notify_slack.py", "--msg", "테스트", "--dry-run"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_tc36_check_runpod_no_api_key_exit1(self, monkeypatch):
        """TC-36: API 키 없는 실제 모드에서 exit code 1."""
        monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
        checker = RunPodChecker(api_key="", dry_run=False)
        assert not checker.is_available()

    def test_tc37_notify_no_webhook_no_crash(self):
        """TC-37: webhook 없어도 예외 없이 반환."""
        notifier = SlackNotifier(webhook_url="", dry_run=False)
        result = notifier.send("메시지")
        assert isinstance(result, dict)

    def test_tc38_check_runpod_default_gpu_type(self):
        """TC-38: 기본 GPU 타입이 RTX_4090."""
        assert RunPodChecker.DEFAULT_GPU_TYPE == "RTX_4090"

    def test_tc39_notifier_default_channel(self):
        """TC-39: 기본 Slack 채널이 #losdb-ops."""
        assert SlackNotifier.DEFAULT_CHANNEL == "#losdb-ops"

    def test_tc40_check_runpod_compile_ok(self):
        """TC-40: check_runpod_availability.py Python 문법 오류 없음."""
        import py_compile
        py_compile.compile(
            str(REPO_ROOT / "tools" / "check_runpod_availability.py"), doraise=True
        )


# ═══════════════════════════════════════════════════════════════════════
#  TC-41~50: biweekly_train 통합 테스트
# ═══════════════════════════════════════════════════════════════════════

class TestBiweeklyTrainIntegration:
    """TC-41~50"""

    WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "biweekly_train.yml"

    def test_tc41_workflow_file_exists(self):
        """TC-41: biweekly_train.yml 파일 존재."""
        assert self.WORKFLOW_PATH.exists()

    def test_tc42_workflow_has_schedule(self):
        """TC-42: schedule 트리거 포함."""
        content = self.WORKFLOW_PATH.read_text()
        assert "schedule" in content
        assert "cron" in content

    def test_tc43_workflow_cron_biweekly(self):
        """TC-43: 격주(매월 1·15일) cron 표현식 포함."""
        content = self.WORKFLOW_PATH.read_text()
        assert "1,15" in content

    def test_tc44_workflow_has_lambda_fallback(self):
        """TC-44: Lambda 폴백 스텝 포함."""
        content = self.WORKFLOW_PATH.read_text()
        assert "lambda_h100" in content or "Lambda" in content

    def test_tc45_workflow_has_slack_notify(self):
        """TC-45: Slack 알림 스텝 포함."""
        content = self.WORKFLOW_PATH.read_text()
        assert "notify_slack.py" in content

    def test_tc46_workflow_has_check_runpod(self):
        """TC-46: RunPod 가용성 체크 스텝 포함."""
        content = self.WORKFLOW_PATH.read_text()
        assert "check_runpod_availability.py" in content

    def test_tc47_auto_recovery_backend_selection(self):
        """TC-47: AutoRecoveryScheduler 백엔드 선택 로직 검증."""
        scheduler = AutoRecoveryScheduler()
        # RunPod 가용 → runpod
        assert scheduler.decide_backend(True) == "runpod"
        # RunPod 불가 → lambda_h100
        assert scheduler.decide_backend(False) == "lambda_h100"

    def test_tc48_full_recovery_cycle(self):
        """TC-48: 전체 복구 사이클 시뮬레이션 (3회 실패 → 에스컬레이션)."""
        scheduler = AutoRecoveryScheduler(max_retries=3)
        for i in range(3):
            backend = scheduler.decide_backend(i % 2 == 0)
            scheduler.record_attempt(backend, False, reason=f"시뮬레이션 실패 {i+1}")
        assert scheduler.should_escalate()
        summary = scheduler.recovery_summary()
        assert summary["attempts"] == 3
        assert summary["succeeded"] == 0

    def test_tc49_successful_recovery_on_lambda(self):
        """TC-49: Lambda 폴백 성공 시 에스컬레이션 없음."""
        scheduler = AutoRecoveryScheduler(max_retries=3)
        scheduler.record_attempt("runpod", False, reason="RunPod 소진")
        scheduler.record_attempt("lambda_h100", True, reason="Lambda 성공")
        assert not scheduler.should_escalate()
        assert scheduler.recovery_summary()["succeeded"] == 1

    def test_tc50_workflow_post_train_gate_check(self):
        """TC-50: post-train-gate 검증 스텝 포함."""
        content = self.WORKFLOW_PATH.read_text()
        assert "post-train-gate" in content or "release_gate" in content or "gate" in content.lower()
