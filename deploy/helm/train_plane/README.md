# Literary OS TrainPlane Helm Chart

**버전**: 0.1.0 (V597, v10.2.0)  
**참조**: ADR-057, Phase B 본안 보강 B-M-16

## 개요

TrainPlane은 LoRA 학습 워크로드를 ServePlane과 완전히 격리하는 Kubernetes Helm Chart 스텁이다.

### 핵심 원칙 (ADR-057 §5)

- **네임스페이스 격리**: `literary-train` (학습) / `literary-serve` (추론) 분리
- **GPU 리소스 독점**: 학습 Job은 ServePlane의 추론 GPU와 공유하지 않음
- **격주 학습 CronJob**: 매 2주 월요일 02:00 KST 풀 학습 자동 트리거
- **주간 미세조정 CronJob**: 매주 수요일 02:00 KST 미세조정 자동 트리거
- **비용 SLO**: 월 $96 목표 (soft $90 → WARN, hard $120 → BLOCK, emergency $150 → HALT)

## 설치 (스텁 — 실 클러스터 연결 시 활성화)

```bash
# 네임스페이스 생성
kubectl create namespace literary-train

# 설치
helm install literary-trainer deploy/helm/train_plane/ \
  --namespace literary-train \
  --set loraJob.baseModel="meta-llama/Llama-3.1-8B"

# 상태 확인
helm status literary-trainer -n literary-train
```

## 주요 Values

| Key | Default | 설명 |
|-----|---------|------|
| `loraJob.loraRank` | `16` | LoRA rank (B-M-05) |
| `loraJob.baseModel` | `meta-llama/Llama-3.1-8B` | 기반 모델 (B-M-04) |
| `costSlo.monthlyTargetUsd` | `96.0` | 월 목표 비용 (B-M-06) |
| `namespace` | `literary-train` | 학습 전용 네임스페이스 |

## Phase B 로드맵

- **V597** (현재): TrainPlane 스텁 + LoRAJobRunner 구현
- **V598**: LoRAModelRegistry + InferenceGateway (ServePlane 연동)
- **V626**: ServePlane Helm 검증 (SP-B.4)
