# Phase 3 — V451~V480 Production Multi-tenant Blueprint

> **합의안 v2.0** (2026-05-15) — CSPE 감수 통과 · 3인 전문가 최종 합의

## 문서

- [`PROPOSAL_v2.docx`](PROPOSAL_v2.docx) — 합의안 제안서 v2.0
- [`DESIGN_v2.docx`](DESIGN_v2.docx) — 시스템 설계도 v2.0

## 한눈에 보기

Phase 2 (V431~V450, Release Gate 14/14 PASS)를 계승하여 V451~V480 30 버전·5 SubPhase로 진화. 핵심 목표는 (1) 실 LLM API 연결, (2) 멀티테넌트 인프라, (3) GDPR/PIPA/EU AI Act + 한국 AI 기본법 컴플라이언스, (4) LoRA 자체호스팅 POC, (5) 공개 출시 + DR.

## v1 → v2 변경 핵심 (20건)

| # | 범주 | v1 | v2 |
|---|---|---|---|
| C-01 | ADR 번호 | 011~015 / 010~014 충돌 | **011~019 단일 시퀀스 (9건)** |
| C-02 | Gate 카운트 | 12 → 17 또는 19 모호 | **19/19 단일화 (Phase 2 14 + Phase 3 5)** |
| C-03 | RPO | 24h | **1h** |
| C-04 | 결제 PG | Stripe만 | **Stripe + 토스페이먼츠** |
| C-05 | 데이터 주권 | 미정 | **ADR-016 (KR/EU/US 리전 라우팅)** |
| C-06 | PII 정확도 | 95% | **SP3 한국어 90% / Phase 4 95%** |
| C-07 | 카나리 KPI | SP4 일회성 | **5분 윈도우 + 자동 롤백 (ADR-017)** |
| C-08 | 파인튜닝 | OpenAI API 우선 | **LoRA 자체호스팅 1순위** |
| C-10 | 일정 | 30주 | **32주 (+2주 마진)** |
| C-11 | NPS | +40 | **+30 1차 / +40 stretch** |

(전체 20건은 PROPOSAL_v2.docx §1 변경 이력 참조.)

## 9개 ADR (Phase 3 신설)

| ADR | 제목 | 버전 |
|---|---|---|
| ADR-011 | Multi-tenant Architecture | V457 |
| ADR-012 | Billing & PG 다중화 | V459 |
| ADR-013 | EU AI Act + 한국 AI 기본법 | V464 |
| ADR-014 | Fine-tuning Policy | V469 |
| ADR-015 | Production SLO v2 | V479 |
| ADR-016 | Data Residency | V467 |
| ADR-017 | Canary KPI Monitor | V472 |
| ADR-018 | SubPhase Rollback Policy | V461 |
| ADR-019 | PII KR Accuracy | V465 |

## 5개 SubPhase 마일스톤

| 마일스톤 | 목표 | 시점 |
|---|---|---|
| M3.0 | Phase 3 키오프 | 2026-11-07 |
| M3.1 | Real LLM 라이브 | 2026-12-26 |
| M3.2 | 멀티테넌트 + DR | 2027-02-13 |
| M3.3 | 컴플라이언스 + 주권 | 2027-04-03 |
| M3.4 | LoRA POC | 2027-05-15 |
| M3.5 | Phase 3 종료 | 2027-06-19 |

## 시작 전 확인

이 로드맵은 **V580 안정화가 먼저 완료된 후** 키오프하는 것을 전제로 한다. V574 → V580 안정화 로드맵은 [`../v575_v580_stabilization/`](../v575_v580_stabilization/)을 참조한다.
