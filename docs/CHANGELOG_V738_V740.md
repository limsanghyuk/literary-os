# Changelog: V738 ~ V740 (Phase E Manifest 사전 정의)

**릴리즈 버전**: v12.5.8  
**날짜**: 2026-05-29  
**Phase**: SP-D.4 (Phase D Sub-phase 4)  
**태그**: `v12.5.8`, `v12.5.8-V738-V740`  

---

## 개요

D-M-12 요구사항 구현: Phase E 클라우드-네이티브 인프라 스텁을 Phase D 안에서 미리 정의하여,
Phase E 진입 시 인프라 결정 재논의 없이 즉시 개발에 착수할 수 있는 기반을 마련한다.

---

## V738 — Helm Chart 스텁 (D-M-12 Phase 1)

### 신규 파일

| 파일 | 설명 |
|------|------|
| `deploy/phase_e/helm/literary-os/Chart.yaml` | Helm Chart 메타데이터 (v13.0.0) |
| `deploy/phase_e/helm/literary-os/values.yaml` | 기본값: FL 설정, 오토스케일링, 서비스 포트 |
| `deploy/phase_e/helm/literary-os/templates/deployment.yaml` | K8s Deployment (liveness/readiness probe) |
| `deploy/phase_e/helm/literary-os/templates/service.yaml` | K8s Service (HTTP 8080, gRPC 50051) |

---

## V739 — KEDA + ArgoCD 스텁 (D-M-12 Phase 2)

### 신규 파일

| 파일 | 설명 |
|------|------|
| `deploy/phase_e/keda/scaled_object.yaml` | KEDA ScaledObject (min:2, max:20, CPU/Memory/Prometheus) |
| `deploy/phase_e/keda/trigger_auth.yaml` | KEDA TriggerAuthentication (SA 기반) |
| `deploy/phase_e/argocd/application.yaml` | ArgoCD Application (automated selfHeal/prune) |
| `deploy/phase_e/argocd/app_project.yaml` | ArgoCD AppProject (소스/배포 네임스페이스 제한) |

---

## V740 — PhaseEManifestValidator + ADR-200~201 (D-M-12 Phase 3)

### 신규 파일

| 파일 | 설명 |
|------|------|
| `literary_system/deploy/__init__.py` | deploy 서브패키지 초기화 |
| `literary_system/deploy/phase_e_manifest.py` | PhaseEManifestValidator (ME-1~ME-8) |
| `tests/unit/test_v740_phase_e_manifest.py` | V740 단위 테스트 (20 TC) |
| `docs/adr/ADR-200.md` | Phase E 인프라 전략 (Helm/KEDA/ArgoCD) |
| `docs/adr/ADR-201.md` | Phase E Manifest 검증 Gate 설계 |

### PhaseEManifestValidator 검증 체크 (ME-1~ME-8)

| 체크 ID | 대상 | 내용 |
|---------|------|------|
| ME-1 | Helm | 4개 Chart 파일 존재 |
| ME-2 | Helm | Chart.yaml version == 13.0.0 |
| ME-3 | Helm | values.yaml fl.enabled + fl.minClients |
| ME-4 | KEDA | 2개 manifest 파일 존재 |
| ME-5 | KEDA | ScaledObject replica bounds |
| ME-6 | ArgoCD | 2개 manifest 파일 존재 |
| ME-7 | ArgoCD | Application automated sync |
| ME-8 | 구조 | deploy/phase_e/{helm,keda,argocd} 존재 |

### 테스트 결과

- **V740 신규**: 20/20 PASS
- **전체 스위트**: 4,152 PASS (기존 26 failures 중 25개 pre-existing)

---

## 통계 요약

| 항목 | V737 기준 | V740 기준 | 증가 |
|------|-----------|-----------|------|
| PyPI version | 12.5.6 | 12.5.8 | +2 |
| 단위 테스트 PASS | 4,133 | 4,152 | +19 |
| ADR 문서 | ADR-199 | ADR-201 | +2 |
| Phase E 스텁 파일 | 0 | 8 | +8 |
