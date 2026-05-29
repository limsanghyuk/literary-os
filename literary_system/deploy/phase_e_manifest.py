"""Phase E manifest validator (V740, D-M-12).

Validates that all required Phase E infrastructure manifests
(Helm, KEDA, ArgoCD) exist on disk and have the correct structure.

ADR-200: Phase E Infrastructure Strategy
ADR-201: Phase E Manifest Validation Gate
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Check result
# ---------------------------------------------------------------------------

@dataclass
class ManifestCheckResult:
    """Result of a single manifest check."""

    check_id: str
    description: str
    passed: bool
    message: str
    manifest_path: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "passed": self.passed,
            "message": self.message,
            "manifest_path": self.manifest_path,
        }


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class PhaseEManifestValidator:
    """Validates Phase E deployment manifests.

    Checks that all required YAML/Helm files exist and contain
    the expected keys for Phase E (v13.0.0) deployment.

    Args:
        repo_root: Root directory of the literary-os repository.
                   Defaults to the parent directory of this file's package root.
    """

    _REQUIRED_HELM_FILES = [
        "deploy/phase_e/helm/literary-os/Chart.yaml",
        "deploy/phase_e/helm/literary-os/values.yaml",
        "deploy/phase_e/helm/literary-os/templates/deployment.yaml",
        "deploy/phase_e/helm/literary-os/templates/service.yaml",
    ]

    _REQUIRED_KEDA_FILES = [
        "deploy/phase_e/keda/scaled_object.yaml",
        "deploy/phase_e/keda/trigger_auth.yaml",
    ]

    _REQUIRED_ARGOCD_FILES = [
        "deploy/phase_e/argocd/application.yaml",
        "deploy/phase_e/argocd/app_project.yaml",
    ]

    def __init__(self, repo_root: Optional[str] = None) -> None:
        if repo_root is None:
            # literary_system/deploy/phase_e_manifest.py → repo root is 2 levels up
            repo_root = str(Path(__file__).resolve().parent.parent.parent)
        self._root = Path(repo_root)
        self._results: List[ManifestCheckResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_all_checks(self) -> Dict:
        """Run all manifest checks and return a summary dict."""
        self._results = []

        self._check_helm_files_exist()
        self._check_chart_version()
        self._check_values_fl_enabled()
        self._check_keda_files_exist()
        self._check_keda_scaled_object()
        self._check_argocd_files_exist()
        self._check_argocd_application()
        self._check_directory_structure()

        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        failed = total - passed

        return {
            "validator": "PhaseEManifestValidator",
            "version": "V740",
            "repo_root": str(self._root),
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "all_passed": failed == 0,
            "checks": [r.to_dict() for r in self._results],
            "summary": f"{passed}/{total} checks passed",
        }

    @property
    def results(self) -> List[ManifestCheckResult]:
        return list(self._results)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_helm_files_exist(self) -> None:
        """ME-1: All required Helm files must exist."""
        missing = []
        for rel_path in self._REQUIRED_HELM_FILES:
            if not (self._root / rel_path).exists():
                missing.append(rel_path)
        if missing:
            self._results.append(ManifestCheckResult(
                check_id="ME-1",
                description="Helm chart files exist",
                passed=False,
                message=f"Missing: {missing}",
            ))
        else:
            self._results.append(ManifestCheckResult(
                check_id="ME-1",
                description="Helm chart files exist",
                passed=True,
                message=f"All {len(self._REQUIRED_HELM_FILES)} Helm files present",
            ))

    def _check_chart_version(self) -> None:
        """ME-2: Chart.yaml must declare version 13.0.0."""
        chart_path = self._root / "deploy/phase_e/helm/literary-os/Chart.yaml"
        if not chart_path.exists():
            self._results.append(ManifestCheckResult(
                check_id="ME-2",
                description="Chart.yaml version == 13.0.0",
                passed=False,
                message="Chart.yaml not found",
                manifest_path=str(chart_path),
            ))
            return
        content = chart_path.read_text(encoding="utf-8")
        match = re.search(r"^version:\s*(.+)$", content, re.MULTILINE)
        if match and match.group(1).strip() == "13.0.0":
            self._results.append(ManifestCheckResult(
                check_id="ME-2",
                description="Chart.yaml version == 13.0.0",
                passed=True,
                message="version: 13.0.0 confirmed",
                manifest_path=str(chart_path),
            ))
        else:
            found = match.group(1).strip() if match else "not found"
            self._results.append(ManifestCheckResult(
                check_id="ME-2",
                description="Chart.yaml version == 13.0.0",
                passed=False,
                message=f"Expected 13.0.0, found: {found}",
                manifest_path=str(chart_path),
            ))

    def _check_values_fl_enabled(self) -> None:
        """ME-3: values.yaml must have fl.enabled and fl.minClients."""
        values_path = self._root / "deploy/phase_e/helm/literary-os/values.yaml"
        if not values_path.exists():
            self._results.append(ManifestCheckResult(
                check_id="ME-3",
                description="values.yaml FL configuration present",
                passed=False,
                message="values.yaml not found",
                manifest_path=str(values_path),
            ))
            return
        content = values_path.read_text(encoding="utf-8")
        has_fl_section = "fl:" in content
        has_enabled = "enabled:" in content
        has_min_clients = "minClients:" in content
        if has_fl_section and has_enabled and has_min_clients:
            self._results.append(ManifestCheckResult(
                check_id="ME-3",
                description="values.yaml FL configuration present",
                passed=True,
                message="fl.enabled + fl.minClients found",
                manifest_path=str(values_path),
            ))
        else:
            missing_keys = []
            if not has_fl_section:
                missing_keys.append("fl:")
            if not has_enabled:
                missing_keys.append("enabled:")
            if not has_min_clients:
                missing_keys.append("minClients:")
            self._results.append(ManifestCheckResult(
                check_id="ME-3",
                description="values.yaml FL configuration present",
                passed=False,
                message=f"Missing keys: {missing_keys}",
                manifest_path=str(values_path),
            ))

    def _check_keda_files_exist(self) -> None:
        """ME-4: All required KEDA files must exist."""
        missing = []
        for rel_path in self._REQUIRED_KEDA_FILES:
            if not (self._root / rel_path).exists():
                missing.append(rel_path)
        if missing:
            self._results.append(ManifestCheckResult(
                check_id="ME-4",
                description="KEDA manifest files exist",
                passed=False,
                message=f"Missing: {missing}",
            ))
        else:
            self._results.append(ManifestCheckResult(
                check_id="ME-4",
                description="KEDA manifest files exist",
                passed=True,
                message=f"All {len(self._REQUIRED_KEDA_FILES)} KEDA files present",
            ))

    def _check_keda_scaled_object(self) -> None:
        """ME-5: KEDA ScaledObject must declare minReplicaCount and maxReplicaCount."""
        so_path = self._root / "deploy/phase_e/keda/scaled_object.yaml"
        if not so_path.exists():
            self._results.append(ManifestCheckResult(
                check_id="ME-5",
                description="KEDA ScaledObject has replica bounds",
                passed=False,
                message="scaled_object.yaml not found",
                manifest_path=str(so_path),
            ))
            return
        content = so_path.read_text(encoding="utf-8")
        has_min = "minReplicaCount:" in content
        has_max = "maxReplicaCount:" in content
        has_kind = "ScaledObject" in content
        if has_kind and has_min and has_max:
            self._results.append(ManifestCheckResult(
                check_id="ME-5",
                description="KEDA ScaledObject has replica bounds",
                passed=True,
                message="kind:ScaledObject + minReplicaCount + maxReplicaCount found",
                manifest_path=str(so_path),
            ))
        else:
            missing = []
            if not has_kind:
                missing.append("kind:ScaledObject")
            if not has_min:
                missing.append("minReplicaCount")
            if not has_max:
                missing.append("maxReplicaCount")
            self._results.append(ManifestCheckResult(
                check_id="ME-5",
                description="KEDA ScaledObject has replica bounds",
                passed=False,
                message=f"Missing: {missing}",
                manifest_path=str(so_path),
            ))

    def _check_argocd_files_exist(self) -> None:
        """ME-6: All required ArgoCD files must exist."""
        missing = []
        for rel_path in self._REQUIRED_ARGOCD_FILES:
            if not (self._root / rel_path).exists():
                missing.append(rel_path)
        if missing:
            self._results.append(ManifestCheckResult(
                check_id="ME-6",
                description="ArgoCD manifest files exist",
                passed=False,
                message=f"Missing: {missing}",
            ))
        else:
            self._results.append(ManifestCheckResult(
                check_id="ME-6",
                description="ArgoCD manifest files exist",
                passed=True,
                message=f"All {len(self._REQUIRED_ARGOCD_FILES)} ArgoCD files present",
            ))

    def _check_argocd_application(self) -> None:
        """ME-7: ArgoCD Application must have automated sync policy."""
        app_path = self._root / "deploy/phase_e/argocd/application.yaml"
        if not app_path.exists():
            self._results.append(ManifestCheckResult(
                check_id="ME-7",
                description="ArgoCD Application has automated sync",
                passed=False,
                message="application.yaml not found",
                manifest_path=str(app_path),
            ))
            return
        content = app_path.read_text(encoding="utf-8")
        has_app_kind = "Application" in content
        has_automated = "automated:" in content
        has_self_heal = "selfHeal:" in content
        if has_app_kind and has_automated and has_self_heal:
            self._results.append(ManifestCheckResult(
                check_id="ME-7",
                description="ArgoCD Application has automated sync",
                passed=True,
                message="kind:Application + automated + selfHeal found",
                manifest_path=str(app_path),
            ))
        else:
            missing = []
            if not has_app_kind:
                missing.append("kind:Application")
            if not has_automated:
                missing.append("automated:")
            if not has_self_heal:
                missing.append("selfHeal:")
            self._results.append(ManifestCheckResult(
                check_id="ME-7",
                description="ArgoCD Application has automated sync",
                passed=False,
                message=f"Missing: {missing}",
                manifest_path=str(app_path),
            ))

    def _check_directory_structure(self) -> None:
        """ME-8: Phase E directory structure must have helm/, keda/, argocd/ subdirs."""
        base = self._root / "deploy/phase_e"
        required_dirs = ["helm", "keda", "argocd"]
        missing = [d for d in required_dirs if not (base / d).is_dir()]
        if missing:
            self._results.append(ManifestCheckResult(
                check_id="ME-8",
                description="Phase E directory structure valid",
                passed=False,
                message=f"Missing directories: {missing}",
            ))
        else:
            self._results.append(ManifestCheckResult(
                check_id="ME-8",
                description="Phase E directory structure valid",
                passed=True,
                message="deploy/phase_e/{helm,keda,argocd} all present",
            ))
