"""V741~V743: Disaster Recovery Gate テスト (40 TC)

ADR-202~204: DRBackupManager / DRRestoreManager / G91 DR Gate DR-1~DR-5
"""
import time
import uuid

import pytest

from literary_system.disaster_recovery.backup_manager import (
    BackupRecord,
    BackupStatus,
    DRBackupManager,
)
from literary_system.disaster_recovery.restore_manager import (
    DRRestoreManager,
    RestoreRecord,
    RestoreStatus,
)
from literary_system.gates.dr_gate import (
    DRCheckResult,
    check_dr1_rpo_enforcement,
    check_dr2_backup_creation,
    check_dr3_rpo_compliance,
    check_dr4_restore_and_verify,
    check_dr5_e2e_pipeline,
    run_dr_gate,
)


# ===========================================================================
# TC01~TC10: DRBackupManager 생성자 및 RPO 검증
# ===========================================================================

class TestDRBackupManagerInit:
    def test_tc01_default_interval_3600(self):
        """TC01: 기본 backup_interval_seconds = 3600."""
        mgr = DRBackupManager()
        assert mgr.interval == 3600

    def test_tc02_custom_interval_accepted(self):
        """TC02: 유효 인터벌 (1800)이 허용된다."""
        mgr = DRBackupManager(backup_interval_seconds=1800)
        assert mgr.interval == 1800

    def test_tc03_interval_3600_boundary_accepted(self):
        """TC03: 경계값 3600s 허용."""
        mgr = DRBackupManager(backup_interval_seconds=3600)
        assert mgr.interval == 3600

    def test_tc04_interval_3601_raises_valueerror(self):
        """TC04: 3601s 초과 시 ValueError (RPO violation)."""
        with pytest.raises(ValueError, match="3601|RPO"):
            DRBackupManager(backup_interval_seconds=3601)

    def test_tc05_interval_zero_raises_valueerror(self):
        """TC05: interval=0 → ValueError."""
        with pytest.raises(ValueError):
            DRBackupManager(backup_interval_seconds=0)

    def test_tc06_interval_negative_raises_valueerror(self):
        """TC06: interval=-1 → ValueError."""
        with pytest.raises(ValueError):
            DRBackupManager(backup_interval_seconds=-1)

    def test_tc07_max_retained_default(self):
        """TC07: 기본 max_retained_backups = 24."""
        mgr = DRBackupManager()
        assert mgr.max_retained == 24

    def test_tc08_custom_max_retained(self):
        """TC08: max_retained_backups 커스텀."""
        mgr = DRBackupManager(max_retained_backups=5)
        assert mgr.max_retained == 5

    def test_tc09_prune_enforces_max_retained(self):
        """TC09: backup_count가 max_retained 초과 시 가장 오래된 항목 제거."""
        mgr = DRBackupManager(backup_interval_seconds=3600, max_retained_backups=3)
        for i in range(5):
            mgr.create_backup("t1", f"data-{i}".encode())
        assert mgr.backup_count("t1") <= 3

    def test_tc10_separate_tenant_records(self):
        """TC10: 테넌트 A의 백업이 테넌트 B 목록에 나타나지 않는다."""
        mgr = DRBackupManager()
        mgr.create_backup("ta", b"a-data")
        mgr.create_backup("tb", b"b-data")
        a_ids = {r.backup_id for r in mgr.list_backups("ta")}
        b_ids = {r.backup_id for r in mgr.list_backups("tb")}
        assert a_ids.isdisjoint(b_ids)


# ===========================================================================
# TC11~TC20: 백업 생성 및 조회
# ===========================================================================

class TestDRBackupManagerCreate:
    def setup_method(self):
        self.mgr = DRBackupManager(backup_interval_seconds=3600)

    def test_tc11_create_returns_success(self):
        """TC11: create_backup() → BackupStatus.SUCCESS."""
        r = self.mgr.create_backup("t", b"data")
        assert r.status == BackupStatus.SUCCESS

    def test_tc12_checksum_is_64_hex(self):
        """TC12: checksum은 64자 SHA-256 hex."""
        r = self.mgr.create_backup("t", b"hello")
        assert r.checksum is not None and len(r.checksum) == 64

    def test_tc13_size_bytes_correct(self):
        """TC13: size_bytes가 데이터 길이와 일치한다."""
        data = b"literary-os-backup"
        r = self.mgr.create_backup("t", data)
        assert r.size_bytes == len(data)

    def test_tc14_completed_at_set(self):
        """TC14: completed_at이 None이 아니다."""
        r = self.mgr.create_backup("t", b"x")
        assert r.completed_at is not None

    def test_tc15_list_backups_most_recent_first(self):
        """TC15: list_backups()는 최신 순 정렬."""
        for _ in range(3):
            self.mgr.create_backup("t", b"d")
        backups = self.mgr.list_backups("t")
        timestamps = [r.created_at for r in backups]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_tc16_latest_backup_is_most_recent(self):
        """TC16: latest_backup()이 가장 최근 SUCCESS 레코드를 반환."""
        r1 = self.mgr.create_backup("t", b"v1")
        r2 = self.mgr.create_backup("t", b"v2")
        latest = self.mgr.latest_backup("t")
        assert latest is not None
        assert latest.backup_id == r2.backup_id

    def test_tc17_rpo_compliant_true_immediately(self):
        """TC17: 방금 만든 백업 → rpo_compliant = True."""
        self.mgr.create_backup("tc", b"d")
        assert self.mgr.rpo_compliant("tc", reference_time=time.time())

    def test_tc18_rpo_compliant_false_at_3601(self):
        """TC18: 3601초 후 rpo_compliant = False."""
        self.mgr.create_backup("tc", b"d")
        assert not self.mgr.rpo_compliant("tc", reference_time=time.time() + 3601)

    def test_tc19_rpo_compliant_false_no_backup(self):
        """TC19: 백업 없는 테넌트 → rpo_compliant = False."""
        assert not self.mgr.rpo_compliant("empty-tenant")

    def test_tc20_to_dict_has_required_keys(self):
        """TC20: BackupRecord.to_dict() 필수 키 7종."""
        r = self.mgr.create_backup("t", b"d")
        d = r.to_dict()
        for key in ("backup_id", "tenant_id", "status", "created_at",
                    "completed_at", "size_bytes", "checksum"):
            assert key in d


# ===========================================================================
# TC21~TC28: DRRestoreManager
# ===========================================================================

class TestDRRestoreManager:
    def setup_method(self):
        self.backup_mgr = DRBackupManager(backup_interval_seconds=3600)
        self.restore_mgr = DRRestoreManager(max_restore_seconds=3600)
        self.data = b"restore-test-payload"
        self.record = self.backup_mgr.create_backup("t", self.data)

    def test_tc21_restore_success(self):
        """TC21: 정확한 데이터로 복원 → RestoreStatus.SUCCESS."""
        rr = self.restore_mgr.restore(self.record, self.data)
        assert rr.status == RestoreStatus.SUCCESS

    def test_tc22_restore_checksum_mismatch(self):
        """TC22: 변조 데이터 → RestoreStatus.CHECKSUM_MISMATCH."""
        rr = self.restore_mgr.restore(self.record, b"tampered")
        assert rr.status == RestoreStatus.CHECKSUM_MISMATCH

    def test_tc23_restore_duration_non_negative(self):
        """TC23: duration_seconds ≥ 0."""
        rr = self.restore_mgr.restore(self.record, self.data)
        assert rr.duration_seconds is not None
        assert rr.duration_seconds >= 0

    def test_tc24_restore_record_has_ids(self):
        """TC24: RestoreRecord에 restore_id, backup_id, tenant_id가 있다."""
        rr = self.restore_mgr.restore(self.record, self.data)
        assert rr.restore_id
        assert rr.backup_id == self.record.backup_id
        assert rr.tenant_id == self.record.tenant_id

    def test_tc25_restore_to_dict_shape(self):
        """TC25: RestoreRecord.to_dict() 필수 키 8종."""
        rr = self.restore_mgr.restore(self.record, self.data)
        d = rr.to_dict()
        for key in ("restore_id", "backup_id", "tenant_id", "status",
                    "started_at", "completed_at", "duration_seconds", "restored_bytes"):
            assert key in d

    def test_tc26_restore_no_checksum_skip(self):
        """TC26: verify_checksum=False → 항상 SUCCESS."""
        rr = self.restore_mgr.restore(self.record, b"any-data", verify_checksum=False)
        assert rr.status == RestoreStatus.SUCCESS

    def test_tc27_restore_invalid_backup_status_fails(self):
        """TC27: PENDING 상태 백업 복원 시도 → FAILED."""
        from literary_system.disaster_recovery.backup_manager import BackupRecord
        bad = BackupRecord(
            backup_id=str(uuid.uuid4()), tenant_id="t",
            status=BackupStatus.PENDING, created_at=time.time(),
            completed_at=None, size_bytes=0, checksum=None, path=None,
        )
        rr = self.restore_mgr.restore(bad, b"d")
        assert rr.status == RestoreStatus.FAILED

    def test_tc28_max_restore_seconds_zero_raises(self):
        """TC28: max_restore_seconds=0 → ValueError."""
        with pytest.raises(ValueError):
            DRRestoreManager(max_restore_seconds=0)


# ===========================================================================
# TC29~TC35: DRCheckResult
# ===========================================================================

class TestDRCheckResult:
    def test_tc29_fields(self):
        """TC29: DRCheckResult 필드 접근."""
        r = DRCheckResult(check_id="DR-1", description="d", passed=True, message="ok")
        assert r.check_id == "DR-1"
        assert r.passed is True

    def test_tc30_to_dict(self):
        """TC30: to_dict() 4개 키."""
        r = DRCheckResult(check_id="DR-2", description="d", passed=False, message="fail")
        d = r.to_dict()
        assert set(d.keys()) == {"check_id", "description", "passed", "message"}
        assert d["passed"] is False

    def test_tc31_dr1_passes(self):
        """TC31: DR-1 RPO enforcement PASS."""
        result = check_dr1_rpo_enforcement()
        assert result.passed, result.message

    def test_tc32_dr2_passes(self):
        """TC32: DR-2 Backup creation PASS."""
        result = check_dr2_backup_creation()
        assert result.passed, result.message

    def test_tc33_dr3_passes(self):
        """TC33: DR-3 RPO compliance PASS."""
        result = check_dr3_rpo_compliance()
        assert result.passed, result.message

    def test_tc34_dr4_passes(self):
        """TC34: DR-4 Restore and verify PASS."""
        result = check_dr4_restore_and_verify()
        assert result.passed, result.message

    def test_tc35_dr5_passes(self):
        """TC35: DR-5 E2E pipeline PASS."""
        result = check_dr5_e2e_pipeline()
        assert result.passed, result.message


# ===========================================================================
# TC36~TC40: G91 run_dr_gate() 통합
# ===========================================================================

class TestRunDrGate:
    @pytest.fixture(autouse=True)
    def gate_result(self):
        self.r = run_dr_gate()

    def test_tc36_gate_approved(self):
        """TC36: G91 approved=True (5/5 PASS)."""
        assert self.r["approved"], self.r["summary"]

    def test_tc37_gate_id_is_g91(self):
        """TC37: gate == 'G91'."""
        assert self.r["gate"] == "G91"

    def test_tc38_version_is_v743(self):
        """TC38: version == 'V743'."""
        assert self.r["version"] == "V743"

    def test_tc39_summary_contains_5_5(self):
        """TC39: summary에 '5/5'가 포함된다."""
        assert "5/5" in self.r["summary"], self.r["summary"]

    def test_tc40_g91_in_gates(self):
        """TC40: G91이 GATES 레지스트리에 등록된다."""
        from literary_system.gates.release_gate import GATES
        gate_keys = [k for k, _, __ in GATES]
        assert "dr_g91" in gate_keys
