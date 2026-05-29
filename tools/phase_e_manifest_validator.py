#!/usr/bin/env python3
"""
Phase E Manifest Validator — ADR-192 (D-M-12 스텁)
====================================================
V740에서 생성하는 Helm + KEDA + ArgoCD manifest의
스키마 유효성을 사전 검증한다.

현재 상태: STUB (V740 구현 전)
V740 구현 시 이 파일에 실제 로직을 추가한다.

필수 필드 명세 (Phase E manifest 구조):
  helm:
    - name: str
    - chart: str
    - namespace: str
    - values: dict
  keda:
    - scaledobject.spec.triggers[].type: str
  argocd:
    - application.spec.source.repoURL: str
    - application.spec.destination.namespace: str
"""
from __future__ import annotations
from typing import Any

REQUIRED_HELM_FIELDS = ["name", "chart", "namespace", "values"]
REQUIRED_ARGOCD_FIELDS = ["spec.source.repoURL", "spec.destination.namespace"]


class ManifestValidationError(ValueError):
    """manifest 스키마 오류."""


def validate_helm_manifest(manifest: dict[str, Any]) -> None:
    """Helm manifest 필수 필드 검증."""
    for field in REQUIRED_HELM_FIELDS:
        if field not in manifest:
            raise ManifestValidationError(f"Helm manifest 누락 필드: '{field}'")


def validate_keda_manifest(manifest: dict[str, Any]) -> None:
    """KEDA ScaledObject manifest 필수 필드 검증."""
    spec = manifest.get("spec", {})
    triggers = spec.get("triggers", [])
    if not triggers:
        raise ManifestValidationError("KEDA manifest: spec.triggers 가 비어있음")
    for i, trigger in enumerate(triggers):
        if "type" not in trigger:
            raise ManifestValidationError(
                f"KEDA manifest: triggers[{i}].type 누락"
            )


def _get_nested(obj: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    cur: Any = obj
    for p in parts:
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def validate_argocd_manifest(manifest: dict[str, Any]) -> None:
    """ArgoCD Application manifest 필수 필드 검증."""
    for field_path in REQUIRED_ARGOCD_FIELDS:
        if _get_nested(manifest, field_path) is None:
            raise ManifestValidationError(
                f"ArgoCD manifest 누락 필드: '{field_path}'"
            )


def validate_phase_e_manifest(
    helm: dict[str, Any],
    keda: dict[str, Any],
    argocd: dict[str, Any],
) -> bool:
    """3종 manifest 통합 검증. PASS → True, FAIL → ManifestValidationError."""
    validate_helm_manifest(helm)
    validate_keda_manifest(keda)
    validate_argocd_manifest(argocd)
    return True


if __name__ == "__main__":
    # 스텁 동작 확인
    print("Phase E Manifest Validator — STUB (V740 구현 대기 중)")
    print("validate_phase_e_manifest(helm, keda, argocd) 인터페이스 준비 완료")
