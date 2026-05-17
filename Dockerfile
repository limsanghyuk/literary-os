# Literary OS Studio API — V430
# Python 3.11 slim 기반, 프로덕션 빌드
FROM python:3.11-slim AS base

LABEL maintainer="literary-os@team.dev"
LABEL version="V430"
LABEL description="Literary OS Studio API — 7-Layer Narrative Engine"

# 비루트 사용자 (보안)
RUN groupadd -r literary && useradd -r -g literary literary

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 먼저 설치 (레이어 캐시 최적화)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 소유권 이전
RUN chown -R literary:literary /app

USER literary

# ── 환경변수 기본값 (프로덕션 안전) ──────────────────────────
# V430 단절 해결: DEV_MODE 기본값을 false 로 설정
ENV LITERARY_OS_DEV_MODE=false
ENV LITERARY_OS_LOCALE=ko
ENV LITERARY_OS_COST_BUDGET_USD=100.0
ENV OAUTH_ISSUER=https://auth.literary-os.dev
ENV OAUTH_AUDIENCE=literary-os-api
ENV OAUTH_ALGORITHMS=RS256
# OTel (선택적 — 미설정 시 콘솔 출력)
ENV OTEL_EXPORTER_OTLP_ENDPOINT=""
ENV OTEL_PROMETHEUS_PORT=9090

EXPOSE 8000 9090

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "apps.studio_api.main:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--log-level", "info"]
