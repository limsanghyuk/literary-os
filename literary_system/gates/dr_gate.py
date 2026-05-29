"""G91 Disaster Recovery Gate (V743, D-M-11, ADR-202~204).

Five DR checks (DR-1 ~ DR-5):
  DR-1  BackupManager construction — RPO enforcement (3601s → ValueError)
  DR-2  Backup creation and checksum integrity
  DR-3  RPO compliance window check (interval ≤ 3600s)
  DR-4  Restore operation and checksum verification
  DR-5  End-to-end DR pipeline (backup → restore → data integrity)

Gate approved when all 5 checks pass.

ADR-202: DR Backup Strategy
ADR-203: G91 DR Gate Design
ADR-204: RPO/RTO Policy
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List

from literary_system.disaster_recovery.backup_manager import (
    BackupStatus,
    DRBackupManager,
)
from literary_system.disaster_recovery.restore_manager import (
    DRRestoreManager,
    RestoreStatus,
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DRCheckResult:
    """Result of a single DR gate check."""

    check_id: str
    description: str
    passed: bool
    message: str

    def to_dict(self) -> Dict:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "passed": self.passed,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# DR-1: RPO enforcement
# ---------------------------------------------------------------------------

def check_dr1_rpo_enforcement() -> DRCheckResult:
    """DR-1: DRBackupManager must reject backup_interval_seconds > 3600."""
    # Valid construction should succeed
    try:
        mgr = DRBackupManager(backup_interval_seconds=3600)
        assert mgr.interval == 3600
    except Exception as exc:
        return DRCheckResult(
            check_id="DR-1",
            description="RPO enforcement (interval ≤ 3600s)",
            passed=False,
            message=f"Valid interval 3600s raised unexpectedly: {exc}",
        )

    # Invalid construction must raise ValueError
    raised = False
    try:
        DRBackupManager(backup_interval_seconds=3601)
    except ValueError as exc:
        if "3601" in str(exc) or "RPO" in str(exc):
            raised = True
        else:
            return DRCheckResult(
                check_id="DR-1",
                description="RPO enforcement (interval ≤ 3600s)",
                passed=False,
                message=f"ValueError raised but wrong message: {exc}",
            )
    except Exception as exc:
        return DRCheckResult(
            check_id="DR-1",
            description="RPO enforcement (interval ≤ 3600s)",
            passed=False,
            message=f"Wrong exception type: {type(exc).__name__}: {exc}",
        )

    if not raised:
        return DRCheckResult(
            check_id="DR-1",
            description="RPO enforcement (interval ≤ 3600s)",
            passed=False,
            message="DRBackupManager(3601) did not raise ValueError",
        )

    return DRCheckResult(
        check_id="DR-1",
        description="RPO enforcement (interval ≤ 3600s)",
        passed=True,
        message="RPO invariant enforced: 3600s allowed, 3601s raises ValueError",
    )


# ---------------------------------------------------------------------------
# DR-2: Backup creation and checksum
# ---------------------------------------------------------------------------

def check_dr2_backup_creation() -> DRCheckResult:
    """DR-2: create_backup() must produce a SUCCESS record with a SHA-256 checksum."""
    mgr = DRBackupManager(backup_interval_seconds=3600)
    data = b"literary-os snapshot data v13"
    record = mgr.create_backup(tenant_id="tenant-a", data=data)

    if record.status != BackupStatus.SUCCESS:
        return DRCheckResult(
            check_id="DR-2",
            description="Backup creation and SHA-256 checksum",
            passed=False,
            message=f"Backup status is {record.status}, expected SUCCESS",
        )
    if not record.checksum or len(record.checksum) != 64:
        return DRCheckResult(
            check_id="DR-2",
            description="Backup creation and SHA-256 checksum",
            passed=False,
            message=f"Invalid checksum: {record.checksum!r}",
        )
    if record.size_bytes != len(data):
        return DRCheckResult(
            check_id="DR-2",
            description="Backup creation and SHA-256 checksum",
            passed=False,
            message=f"size_bytes mismatch: {record.size_bytes} != {len(data)}",
        )

    return DRCheckResult(
        check_id="DR-2",
        description="Backup creation and SHA-256 checksum",
        passed=True,
        message=f"Backup {record.backup_id[:8]}… SUCCESS, checksum={record.checksum[:12]}…",
    )


# ---------------------------------------------------------------------------
# DR-3: RPO compliance window
# ---------------------------------------------------------------------------

def check_dr3_rpo_compliance() -> DRCheckResult:
    """DR-3: rpo_compliant() must return True if latest backup is within interval."""
    mgr = DRBackupManager(backup_interval_seconds=3600)
    tenant = "tenant-rpo"

    # No backup yet → not compliant
    if mgr.rpo_compliant(tenant):
        return DRCheckResult(
            check_id="DR-3",
            description="RPO compliance window check",
            passed=False,
            message="rpo_compliant returned True before any backup",
        )

    mgr.create_backup(tenant_id=tenant, data=b"snapshot")
    ref_time = time.time()

    # Just-created backup → compliant
    if not mgr.rpo_compliant(tenant, reference_time=ref_time):
        return DRCheckResult(
            check_id="DR-3",
            description="RPO compliance window check",
            passed=False,
            message="rpo_compliant returned False immediately after backup",
        )

    # 3601s later → no longer compliant
    if mgr.rpo_compliant(tenant, reference_time=ref_time + 3601):
        return DRCheckResult(
            check_id="DR-3",
            description="RPO compliance window check",
            passed=False,
            message="rpo_compliant returned True 3601s after backup (should be False)",
        )

    return DRCheckResult(
        check_id="DR-3",
        description="RPO compliance window check",
        passed=True,
        message="RPO window: compliant immediately, non-compliant after 3601s",
    )


# ---------------------------------------------------------------------------
# DR-4: Restore and checksum verification
# ---------------------------------------------------------------------------

def check_dr4_restore_and_verify() -> DRCheckResult:
    """DR-4: DRRestoreManager must restore data and verify checksum."""
    mgr = DRBackupManager(backup_interval_seconds=3600)
    restore_mgr = DRRestoreManager(max_restore_seconds=3600)

    data = b"restore-test-payload-literary-os"
    record = mgr.create_backup(tenant_id="tenant-restore", data=data)

    if record.status != BackupStatus.SUCCESS:
        return DRCheckResult(
            check_id="DR-4",
            description="Restore and checksum verification",
            passed=False,
            message=f"Backup prerequisite failed: {record.status}",
        )

    # Correct restore
    rr = restore_mgr.restore(backup=record, data=data, verify_checksum=True)
    if rr.status != RestoreStatus.SUCCESS:
        return DRCheckResult(
            check_id="DR-4",
            description="Restore and checksum verification",
            passed=False,
            message=f"Restore failed: {rr.status} — {rr.error}",
        )

    # Tampered data must trigger checksum mismatch
    tampered = b"tampered-data"
    rr_bad = restore_mgr.restore(backup=record, data=tampered, verify_checksum=True)
    if rr_bad.status != RestoreStatus.CHECKSUM_MISMATCH:
        return DRCheckResult(
            check_id="DR-4",
            description="Restore and checksum verification",
            passed=False,
            message=f"Tampered restore should be CHECKSUM_MISMATCH, got {rr_bad.status}",
        )

    return DRCheckResult(
        check_id="DR-4",
        description="Restore and checksum verification",
        passed=True,
        message="Restore SUCCESS with correct data; CHECKSUM_MISMATCH detected for tampered data",
    )


# ---------------------------------------------------------------------------
# DR-5: End-to-end DR pipeline
# ---------------------------------------------------------------------------

def check_dr5_e2e_pipeline() -> DRCheckResult:
    """DR-5: Full backup → prune → restore pipeline with multi-tenant isolation."""
    backup_mgr = DRBackupManager(backup_interval_seconds=1800, max_retained_backups=3)
    restore_mgr = DRRestoreManager(max_restore_seconds=1800)

    payloads = {
        "tenant-x": b"tenant-x-data-v1",
        "tenant-y": b"tenant-y-data-v1",
    }

    # Create 4 backups for tenant-x (exceeds max_retained=3 → prune triggered)
    for i in range(4):
        backup_mgr.create_backup("tenant-x", f"tenant-x-iter-{i}".encode())

    if backup_mgr.backup_count("tenant-x") > 3:
        return DRCheckResult(
            check_id="DR-5",
            description="E2E DR pipeline (multi-tenant backup + restore)",
            passed=False,
            message=f"Prune failed: {backup_mgr.backup_count('tenant-x')} records (max 3)",
        )

    # Create backup for tenant-y
    rec_y = backup_mgr.create_backup("tenant-y", payloads["tenant-y"])

    # Tenant isolation: tenant-x backups must not appear in tenant-y
    x_ids = {r.backup_id for r in backup_mgr.list_backups("tenant-x")}
    if rec_y.backup_id in x_ids:
        return DRCheckResult(
            check_id="DR-5",
            description="E2E DR pipeline (multi-tenant backup + restore)",
            passed=False,
            message="Tenant isolation failure: tenant-y record appeared in tenant-x",
        )

    # Restore tenant-y
    rr = restore_mgr.restore(backup=rec_y, data=payloads["tenant-y"])
    if rr.status != RestoreStatus.SUCCESS:
        return DRCheckResult(
            check_id="DR-5",
            description="E2E DR pipeline (multi-tenant backup + restore)",
            passed=False,
            message=f"E2E restore failed: {rr.status} — {rr.error}",
        )
    if rr.duration_seconds is None or rr.duration_seconds < 0:
        return DRCheckResult(
            check_id="DR-5",
            description="E2E DR pipeline (multi-tenant backup + restore)",
            passed=False,
            message=f"Invalid duration: {rr.duration_seconds}",
        )

    return DRCheckResult(
        check_id="DR-5",
        description="E2E DR pipeline (multi-tenant backup + restore)",
        passed=True,
        message=(
            f"Prune OK (≤3), tenant isolation OK, "
            f"restore {rr.restore_id[:8]}… SUCCESS in {rr.duration_seconds*1000:.1f}ms"
        ),
    )


# ---------------------------------------------------------------------------
# Gate runner
# ---------------------------------------------------------------------------

_DR_CHECKS = [
    check_dr1_rpo_enforcement,
    check_dr2_backup_creation,
    check_dr3_rpo_compliance,
    check_dr4_restore_and_verify,
    check_dr5_e2e_pipeline,
]


def run_dr_gate() -> Dict:
    """Execute all DR gate checks and return a summary dict."""
    results: List[DRCheckResult] = [fn() for fn in _DR_CHECKS]
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    return {
        "gate": "G91",
        "version": "V743",
        "approved": failed == 0,
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "summary": f"{passed}/{total} DR checks passed",
        "checks": [r.to_dict() for r in results],
    }
