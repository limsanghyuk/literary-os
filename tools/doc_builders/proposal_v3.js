// V621~V630 통합 본안 v3.0 합의 제안서 — SP-B.4 완성 + V620_R 보강 통합
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
} = require('docx');

const border = { style: BorderStyle.SINGLE, size: 4, color: "888888" };
const borders = { top: border, bottom: border, left: border, right: border };

function p(text, opts) { opts = opts || {};
  return new Paragraph({
    spacing: { before: opts.before || 80, after: opts.after || 80 },
    alignment: opts.align,
    children: [new TextRun({ text: text, bold: opts.bold, italics: opts.italics, color: opts.color, size: opts.size || 22, font: "Malgun Gothic" })],
  });
}
function h(text, level) {
  const sizes = { 1: 30, 2: 26, 3: 24 };
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text: text, bold: true, size: sizes[level] || 22, font: "Malgun Gothic" })],
  });
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text: text, size: 22, font: "Malgun Gothic" })],
  });
}
function cell(text, width, opts) { opts = opts || {};
  return new TableCell({
    borders: borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: text, bold: opts.bold, color: opts.color, size: opts.size || 19, font: "Malgun Gothic" })] })],
  });
}
function table(rows, widths, headerFill) {
  headerFill = headerFill || "C5E0F0";
  const total = widths.reduce(function(a,b){return a+b;}, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map(function(row, i) {
      return new TableRow({
        tableHeader: i === 0,
        children: row.map(function(c, j) { return cell(c, widths[j], { fill: i === 0 ? headerFill : undefined, bold: i === 0, size: 18 }); }),
      });
    }),
  });
}

const children = [];

// 표지
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Literary OS", bold: true, size: 40, font: "Malgun Gothic" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "V621 ~ V630 통합 본안 합의 제안서 v3.0", bold: true, size: 32, font: "Malgun Gothic" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "SP-B.4 완성 + V620_R 보강 통합 — Phase B 진정한 종료", size: 24, font: "Malgun Gothic" })] }));
children.push(p(""));
children.push(p("기준선: v10.25.2 (V620-AUDIT2) · 60 Gates · 6,728+ Tests · G61 6축 PASS", { align: AlignmentType.CENTER }));
children.push(p("목표: v11.0.0 (V630) · 60 Gates · G61 6+1축 PASS · 7,228+ Tests · Phase B 완전 종료", { align: AlignmentType.CENTER }));
children.push(p("기반 본안 v2.0: literary_os_v601_v630_phase_b_blueprint_v2.docx (commit f16c5c8)", { align: AlignmentType.CENTER }));
children.push(p("기반 감사: 2026-05-25_phase_b_audit_report.docx (V620 종료 실측)", { align: AlignmentType.CENTER }));
children.push(p("이전 시도 V620_R (supersedes): literary_os_v620_r_proposal/blueprint.docx", { align: AlignmentType.CENTER }));
children.push(p("작성: Chief Architect × Chief Compiler × Chief System Principal Engineer", { align: AlignmentType.CENTER, bold: true }));
children.push(p("2026-05-25", { align: AlignmentType.CENTER }));
children.push(p("기밀 — LOS-V621-V630-PROPOSAL-V3-2026-05-25", { align: AlignmentType.CENTER, italics: true }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// 1. 경영진 요약
children.push(h("1. 경영진 요약", 1));
children.push(p("본 v3.0 제안서는 본안 v2.0 V621~V630 잔여 SP-B.4 항목(6건 미완료 + 3건 부분 완료)과 V620_R 보강 항목(P-IF/conflict_policy/biweekly/Branch/ATIA/v11.0.0)을 하나의 V버전 시리즈로 통합 재설계한 합의 본안이다."));
children.push(p("배경 정정 사실 4건:", { bold: true }));
children.push(bullet("① V620 종료 시점은 SP-B.4 완료가 아닌 SP-B.4 약 35~40% 진행 상태. V621~V630 본안 항목 다수(biweekly/ServePlane Helm/Grafana/운영문서/ATIA/G61 6+1축/v11.0.0) 미완료"));
children.push(bullet("② V620_R PATCH 시리즈는 PATCH가 아닌 V버전 본 작업으로 통합되어야 함 — 본안 v2.0 V621~V630에 이미 포함된 항목이 다수"));
children.push(bullet("③ V630 = Phase B 진정한 종료 = v11.0.0 GitHub Release + G61 6+1축 PASS + Tests 7,000+. 그 후 V631~ Phase C 진입"));
children.push(bullet("④ SP-B.2/B.3 retrofit (P-IF + conflict_policy + workload_profile + adv_seeds)도 SP-B.4 진행과 동시에 V621/V622에 흡수"));
children.push(p(""));
children.push(p("3인 만장일치 결정:", { bold: true }));
children.push(table([
  ["#", "결정", "근거"],
  ["D1", "V621~V630 10 versions 직렬 + V620_R 폐기 (산출물은 참조 보존)", "V버전 통합이 가장 자연스러움. V620_R은 부분 흡수"],
  ["D2", "V621 = SP-B.2 retrofit (AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer)", "Phase C 인터페이스 사전 트레이스 — SP-B.2 종료 V606에서 누락된 사항"],
  ["D3", "V622 = SP-B.3 retrofit (conflict_policy 5종 + workload_profile + adv_seeds 5종)", "SharedCharacterDBV2/MultiWorkOrchestratorV2/RewardModel 보강 — V607/V608에서 누락"],
  ["D4", "V623~V627 = 본안 v2.0 V621~V627 잔여 (Helm 사전 / 24h / biweekly / TrainPlane / ServePlane)", "본안 v2.0 그대로 + V614~V619 산출물 활용"],
  ["D5", "V628 = Grafana + Prometheus dashboard (Cost SLO + Krippendorff α drift)", "본안 v2.0 V628 그대로"],
  ["D6", "V629 = Phase B 운영 문서 (Diataxis 4) + ATIA mini-audit + Branch Protection", "본안 v2.0 V629 + V620_R R6 ATIA + R5 Branch Protection 통합"],
  ["D7", "V630 = G61 6+1축 (C7 verify_interfaces_trace 추가) + v11.0.0 GitHub Release", "본안 v2.0 V630 + V620_R R4 C7 통합. ADR-080 → ADR-097 supersedes"],
  ["D8", "사전 작업 V621-PRE = AGENTS.md/CLAUDE.md/preflight_step15 자동 학습 강제", "V620_R R0 흡수 — Sonnet 4.6 누락 방지"],
  ["D9", "ADR-088~097 10건 신설 (각 V버전 1건) + ADR-PC-IF 통합 신설", "각 V버전 ADR 명시. ADR-080은 ADR-097이 supersedes"],
  ["D10", "Tests +500 (V620 6,728 → V630 7,228+) — 본안 v2.0 +500보다 약간 보수적", "각 V버전 평균 +50 TC. 실측에서 일부 회귀 +50 별도"],
  ["D11", "V630 종료 = Phase B 완전 종료 선언 → Phase C 본안 작성 트리거", "Phase C 본안 v3.0 작성 별도 세션 (상위 연산 모드)"],
  ["D12", "Sonnet 4.6 자동 학습용 .md + .docx 양면 push", "V620_R 실패 원인(handoff .md.docx 오류) 재발 방지"],
], [500, 3000, 5500]));
children.push(p(""));

// 2. V620 종료 시점 정확한 상태 재정리
children.push(h("2. V620 종료 시점 정확한 상태 (감사 결과 재정리)", 1));
children.push(table([
  ["본안 v2.0 V버전", "본안 항목", "V614~V620 허브 실측", "상태"],
  ["V621", "SystemIntegrationTest E2E + Helm 사전 검증", "V613에 E2E 흡수. Helm 사전 검증 부재", "▲ 부분 완료"],
  ["V622", "PerformanceOptimizer + Metrics5Axis 5축", "V614 완료 (p50/p95/p99 확인)", "✅ 완료"],
  ["V623", "24h 장기 실행 + biweekly 시뮬레이션", "V617 LongRunMonitor만. 24h 시나리오/biweekly 부재", "▲ 부분 완료"],
  ["V624", "메모리 누수 검증 (tracemalloc)", "V616 MemoryLeakDetector 완료", "✅ 완료"],
  ["V625", "자동 복구 + biweekly_train.yml + Lambda 폴백", "biweekly_train.yml 부재", "❌ 미완료"],
  ["V626", "TrainPlane Helm 검증", "chart 존재, 검증 워크플로우 부재", "▲ chart만"],
  ["V627", "ServePlane Helm 검증", "deploy/helm/serve_plane/ 부재", "❌ 미완료"],
  ["V628", "Grafana + Prometheus dashboard", "디렉터리 전무", "❌ 미완료"],
  ["V629", "Phase B 운영 문서 + ATIA + Branch Protection", "docs/operations/ + ATIA 도구 + Branch Protection 모두 부재", "❌ 미완료"],
  ["V630", "G61 6+1축 + v11.0.0 Release", "G61 6축만. v10.25.2 (v11.0.0 미달)", "▲ 6축만"],
], [1500, 3000, 3000, 1500]));
children.push(p("실측 완료율: ✅ 2건 / ▲ 4건 / ❌ 4건 = 약 35~40% (가중치 적용 시).", { italics: true }));
children.push(p(""));

// 3. V620_R → v3.0 통합 매핑
children.push(h("3. V620_R 6건 → V621~V630 통합 매핑", 1));
children.push(table([
  ["V620_R", "보강 항목", "v3.0 V버전 흡수", "비고"],
  ["R0", "AGENTS.md/preflight 자동 학습 강제", "V621-PRE (사전 작업)", "Sonnet 4.6 누락 방지 — V버전 진입 전 0.5일"],
  ["R1", "AgentEnvelope (P-IF-01)", "V621", "SP-B.2 retrofit"],
  ["R2", "ReaderFeedbackIngest (P-IF-03)", "V621", "SP-B.2 retrofit"],
  ["R3", "OpenAPI SemVer (P-IF-04)", "V621", "SP-B.2 retrofit"],
  ["R4", "G61 C7축 verify_interfaces_trace", "V630", "본안 v2.0 V630 G61 6+1축에 흡수"],
  ["R5a", "conflict_policy 5종", "V622", "SP-B.3 retrofit"],
  ["R5b", "workload_profile 1/2/3 SLO", "V622", "SP-B.3 retrofit"],
  ["R5c", "adv_seeds 5종", "V622", "SP-B.2 retrofit (RewardModel)"],
  ["R5d-1", "biweekly_train.yml", "V625", "본안 v2.0 V625 그대로"],
  ["R5d-2", "Branch Protection", "V629", "본안 v2.0 V629 운영 정책에 흡수"],
  ["R6-1", "ATIA mini-audit 일괄", "V629", "본안 v2.0 V629 외부 감사 패키지에 흡수"],
  ["R6-2", "v11.0.0 + Tests 7,000+", "V630", "본안 v2.0 V630 그대로"],
], [600, 3500, 1700, 3200]));
children.push(p("결론: V620_R 12건 보강이 V621-PRE + V621 + V622 + V625 + V629 + V630의 6개 V버전에 자연 분산.", { italics: true }));
children.push(p(""));

// 4. 3인 전문가 메타 리뷰
children.push(h("4. 3인 전문가 메타 리뷰", 1));
children.push(h("4.1 Chief Architect — 시스템 경계·인터페이스 진화", 2));
children.push(p("V620까지 안정 + V621~V630에서 외부 인터페이스(Helm/Dashboard/Branch)와 Phase C/D 인터페이스(P-IF) 동시 완성. SP-B.4가 비-기능적(운영/문서/감사) 요구를 중심으로 명확히 분리됨."));
children.push(bullet("V621 SP-B.2 retrofit — AgentEnvelope/ReaderFeedbackIngest/OpenAPI SemVer 3건 동시 (P-IF 표면 일괄 완성)"));
children.push(bullet("V622 SP-B.3 retrofit — conflict_policy/workload_profile/adv_seeds 3건 동시 (MultiWork v2.0 보강)"));
children.push(bullet("V623 Helm 사전 검증 (P-Arch-01) — V626/V627 본 검증 이전 lint + dry-run"));
children.push(bullet("V627 ServePlane Helm 신설 + 검증 — TrainPlane과 격리된 prod 서빙 plane 분리 완성"));
children.push(bullet("V630 G61 6+1축 (C7 verify_interfaces_trace) — Phase B → Phase C 진입 게이트 + ADR-080 → ADR-097 supersedes"));

children.push(h("4.2 Chief Compiler — 평가·CI·재현성·테스트", 2));
children.push(p("v3.0은 V620_R의 PATCH 방식 대신 V버전 신설 방식이라 회귀 테스트 관리가 단순. 각 V버전마다 단일 PR + 단일 ADR + 평균 +50 TC."));
children.push(bullet("V621 +60 TC (AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer 통합 회귀)"));
children.push(bullet("V622 +60 TC (conflict_policy 5종 + workload_profile + adv_seeds 5종)"));
children.push(bullet("V623~V627 +30~50 TC 평균 (각 V버전 신규 모듈 단위 + 통합)"));
children.push(bullet("V628 +30 TC (dashboard 메트릭 export 검증)"));
children.push(bullet("V629 +60 TC (운영 문서 자동 검증 + ATIA + Branch Protection 회귀)"));
children.push(bullet("V630 +50 TC (G61 6+1축 + v11.0.0 일관성 + 회귀 종합)"));
children.push(bullet("총 +500 TC (V620 6,728 → V630 7,228+) — 본안 v2.0 +500 동일"));

children.push(h("4.3 Chief System Principal Engineer — 거버넌스·진화·운영", 2));
children.push(p("V621~V630에서 Phase B의 운영 + 감사 + 문서 + semver 정상화가 완성됨. V630이 진정한 Phase B 종료점이며, 그 후 Phase C 진입은 자연스러운 전환."));
children.push(bullet("V621-PRE (사전 작업, R0 흡수) — AGENTS.md 자동 학습 강제. V620_R 실패 원인 재발 방지"));
children.push(bullet("V625 biweekly_train.yml + Lambda H100 폴백 — 매월 1·15일 02:00 KST 자동. 운영 사이클 정착"));
children.push(bullet("V628 Grafana + Prometheus — Cost SLO + Krippendorff α drift dashboard. RLHF 보상 모델 drift 시각화"));
children.push(bullet("V629 ATIA mini-audit (R6 흡수) — 100건 무작위 + sha256 chain + ATIA 메타데이터 일괄 감리. 외부 감사 준비 완료"));
children.push(bullet("V629 Branch Protection (R5d 흡수) — main sign-off ≥1 + status check (60 Gates + openapi_diff)"));
children.push(bullet("V630 v11.0.0 GitHub Release + Phase B 완전 종료 선언 + KoreanDrama-Suite-v1 HF 비공개 등록"));
children.push(p("진화 방향 추가 제언:", { bold: true }));
children.push(bullet("Phase C 진입 LOI 1건 시도 — V630 종료 후 2개월 이내. Phase C 본안 v3.0 작성 시 P-IF (V621) 활성 전제"));
children.push(bullet("Phase D SDK 공개 준비 — V621 OpenAPI SemVer가 그 기반. Phase D 진입 시 추가 OpenAPI 안정성 검증"));
children.push(bullet("v11.0.0 후속 v11.x patch — Hotfix는 v11.0.x로, 새 기능은 Phase C V631~로 분리"));
children.push(p("문제점·해결책 종합:", { bold: true }));
children.push(table([
  ["#", "잔존 문제 / 우려", "해결책"],
  ["P1", "V620_R 산출물 부분 활용 — 사용자 혼동 가능성", "v3.0에서 V620_R supersedes 명시. 산출물은 참조 보존 (push 안 함)"],
  ["P2", "V621 retrofit이 SP-B.2/B.3 기존 모듈 회귀 유발 가능", "V621 진입 전 V620 전체 회귀 baseline + retrofit 후 동등성 검증"],
  ["P3", "V627 ServePlane Helm 신설이 V605 ModelServing 라우팅 변경 필요할 수 있음", "V627은 chart만 신설 + ingress 룰만. ModelServing 코드 변경 없음"],
  ["P4", "V628 Grafana는 외부 의존성 (Grafana 서버) — Dev 환경 부담", "V628은 dashboard JSON만 commit. 운영 환경은 별도 운영자 deploy"],
  ["P5", "V629 ATIA mini-audit 100건이 통과 안 될 가능성 (sha256 mismatch)", "V629 진행 전 V592 ProvenanceIndex 점검 + 5만 신 sample run 1회"],
  ["P6", "V630 v11.0.0 승격 시 외부 사용자 영향 (현재 없을 듯 하나 확인)", "CHANGELOG에 semver 변경 사유 명시 + 1.0.0 baseline 보장"],
  ["P7", "Sonnet 4.6 자동 학습 누락 재발 가능성 (V620_R 사례)", "V621-PRE에서 AGENTS.md 강제 + preflight_step15 검증 함수 추가"],
  ["P8", "Tests 7,228 미달 가능성", "각 V버전 +50 TC 평균. 부족 시 V630 최종에서 +50 보강"],
], [500, 4500, 4500]));
children.push(p(""));

// 5. V버전별 합의 결정
children.push(h("5. V621~V630 V버전별 합의 결정 + 본안 매핑", 1));
children.push(table([
  ["V", "이름", "기간", "주요 모듈", "ADR", "Tests +"],
  ["V621-PRE", "자동 학습 강제 (R0)", "0.5일", "AGENTS.md + preflight_step15", "-", "+5"],
  ["V621", "SP-B.2 retrofit (P-IF 3건)", "1주", "AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer", "ADR-088", "+60"],
  ["V622", "SP-B.3 retrofit (3건)", "1주", "conflict_policy + workload_profile + adv_seeds", "ADR-089", "+60"],
  ["V623", "SystemIntegrationTest + Helm 사전 검증", "3일", "test_system_integration 확장 + helm lint", "ADR-090", "+30"],
  ["V624", "24h 장기 시나리오 + 메모리 회귀", "3일", "24h test runner + V616/V617 통합 회귀", "ADR-091", "+30"],
  ["V625", "biweekly_train + Lambda 폴백 + 자동 복구", "1주", "biweekly_train.yml + check_runpod + notify_slack + auto_recovery", "ADR-092", "+50"],
  ["V626", "TrainPlane Helm 검증", "3일", "helm test + dry-run + chart lint workflow", "ADR-093", "+30"],
  ["V627", "ServePlane Helm 신설 + 검증", "1주", "deploy/helm/serve_plane/ + Ingress + 검증 workflow", "ADR-094", "+50"],
  ["V628", "Grafana + Prometheus dashboard", "3일", "monitoring/grafana/ JSON + prom scrape config", "ADR-095", "+30"],
  ["V629", "운영 문서 + ATIA + Branch Protection", "1주", "docs/operations/ Diataxis + atia_mini_audit.py + Branch Protection 설정", "ADR-096", "+60"],
  ["V630", "G61 6+1축 + v11.0.0 Release", "3일", "phase_b_exit_gate.py 갱신 + ADR-097 (supersedes ADR-080) + GitHub Release", "ADR-097", "+50 + 회귀 +45"],
], [800, 2500, 700, 3000, 700, 1380]));
children.push(p("총 기간: 약 5주 (R0 사전 + 10 V버전). 본안 v2.0 V621~V630 동일 일정 + V620_R 보강 통합.", { italics: true }));
children.push(p("총 Tests +500 (V620 6,728 → V630 7,228+).", { italics: true }));
children.push(p(""));

// 6. 신규 ADR
children.push(h("6. 신규 ADR 11건 (ADR-088~097 + ADR-PC-IF)", 1));
children.push(table([
  ["ADR", "제목", "V버전", "주요 결정"],
  ["ADR-088", "SP-B.2 retrofit — AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer", "V621", "P-IF-01/03/04 통합 부착. CanonicalBridgeV2 하위 호환 + FastAPI SemVer"],
  ["ADR-089", "SP-B.3 retrofit — conflict_policy + workload_profile + adv_seeds", "V622", "5종 정책 + 1/2/3 SLO + 5종 적대 시드 통합"],
  ["ADR-090", "System Integration + Helm 사전 검증 정책", "V623", "Helm lint + dry-run 사전 + V626/V627 본 검증 분리"],
  ["ADR-091", "24h 장기 시나리오 + 메모리 회귀 자동화", "V624", "scheduled long-run test + tracemalloc 회귀"],
  ["ADR-092", "biweekly_train + Lambda H100 폴백 + 자동 복구", "V625", "매월 1·15일 02:00 KST + RunPod/Lambda 자동 전환"],
  ["ADR-093", "TrainPlane Helm 검증 정책", "V626", "helm test + GitHub Actions chart lint"],
  ["ADR-094", "ServePlane Helm 신설 + 검증 정책", "V627", "deploy/helm/serve_plane/ 신설 + Ingress + ModelServing 연동"],
  ["ADR-095", "Grafana + Prometheus dashboard 표준", "V628", "Cost SLO + Krippendorff α drift 시각화"],
  ["ADR-096", "Phase B 운영 문서 (Diataxis) + ATIA mini-audit + Branch Protection", "V629", "Diataxis 4 카테고리 + 100건 무작위 감리 + main sign-off"],
  ["ADR-097", "Phase B Exit Gate G61 6+1축 + v11.0.0 (supersedes ADR-080)", "V630", "C7 verify_interfaces_trace + semver major"],
  ["ADR-PC-IF", "Phase C/D 인터페이스 트레이스 통합 ADR", "V621/V630", "P-IF-01~05 통합 명세"],
], [800, 4500, 600, 3380]));
children.push(p(""));

// 7. 의존성 그래프
children.push(h("7. 의존성 그래프", 1));
children.push(p("V621-PRE (사전) → V621 → V622 → V623 → V624 → V625 → V626 → V627 → V628 → V629 → V630"));
children.push(p("병렬 가능: V623~V624 (Helm 사전 vs 24h test) / V625~V628 (biweekly vs Helm vs dashboard)", { italics: true }));
children.push(p("필수 순차: V621/V622 (retrofit) → V630 (C7은 V621 retrofit 통과 후만 PASS)", { italics: true }));
children.push(p(""));

// 8. 리스크 레지스터
children.push(h("8. 리스크 레지스터 (v3.0 추가 8건)", 1));
children.push(table([
  ["ID", "리스크", "확률", "영향", "대응"],
  ["R-V3-1", "V621 retrofit이 V606 G56/G57 회귀 유발", "중", "고", "V621 진입 전 baseline + retrofit 후 동등성 검증 + DeprecationWarning 1 시즌 후"],
  ["R-V3-2", "V622 conflict_policy=ESCALATE 기본이 기존 코드 호환성 깨뜨림", "낮음", "중", "default 유지 — 기존 동작과 동일. 새 정책은 명시 호출만"],
  ["R-V3-3", "V625 biweekly_train dry_run 5회 연속 실패", "중", "중", "dry_run 모드 기본 + 실 학습 비활성화 옵션 + 운영자 수동 트리거"],
  ["R-V3-4", "V627 ServePlane Helm 신설이 V605 ModelServing 라우팅 충돌", "낮음", "고", "V627은 chart + ingress만. ModelServing 코드 무변경 강제"],
  ["R-V3-5", "V628 Grafana dashboard JSON 파싱 오류", "낮음", "낮음", "샘플 데이터로 import test + JSON schema 검증"],
  ["R-V3-6", "V629 ATIA mini-audit 100건 sha256 mismatch ≥1건", "중", "고", "V629 진입 전 V592 ProvenanceIndex 점검 + 5만 신 sample run"],
  ["R-V3-7", "V629 Branch Protection 설정이 기존 PR 흐름 차단", "중", "중", "Branch Protection 적용 전 PR 1건 dry-run + 운영자 합의"],
  ["R-V3-8", "V630 v11.0.0 승격 시 외부 의존 라이브러리 호환성 깨짐", "낮음", "중", "CHANGELOG에 SemVer 변경 사유 명시 + downstream 알림"],
], [700, 3500, 700, 700, 3460]));
children.push(p(""));

// 9. 결론
children.push(h("9. 결론 및 서명", 1));
children.push(p("본 V621~V630 통합 본안 v3.0은 본안 v2.0 V621~V630 잔여(6 미완료 + 3 부분) + V620_R 보강(12건) + V620_R 실패 원인 재발 방지(R0 → V621-PRE)를 하나의 V버전 시리즈로 통합한 합의 본안이다."));
children.push(p("v2.0 잔여 + V620_R 통합 핵심 5건:", { bold: true }));
children.push(bullet("[자동 학습] V621-PRE — AGENTS.md/preflight 자동 학습 강제. Sonnet 4.6 누락 방지"));
children.push(bullet("[SP-B.2 retrofit] V621 — AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer (Phase C 진입 cliff 해소)"));
children.push(bullet("[SP-B.3 retrofit] V622 — conflict_policy + workload_profile + adv_seeds (MultiWork v2.0 보강)"));
children.push(bullet("[SP-B.4 잔여] V623~V629 — Helm 사전/검증 + biweekly + dashboard + 운영 문서 + ATIA + Branch Protection"));
children.push(bullet("[Phase B 종료] V630 — G61 6+1축 + v11.0.0 GitHub Release + Phase C 진입 선언"));
children.push(p(""));
children.push(p("V630 종료 시점 Literary OS는 한국 드라마 LoRA v1.0 (8B+3B) + RLHF v1.0 + MultiWork v2.0 + Phase B Exit G61 6+1축 + P-IF-01~05 + conflict_policy 5종 + workload_profile + adv_seeds 5종 + biweekly_train + Branch Protection + TrainPlane/ServePlane Helm + Grafana dashboard + ATIA mini-audit + v11.0.0 / 60 Gates / 7,228+ Tests를 보유한다. Phase C(V631+ 멀티 에이전트 + 실시간 독자 피드백) 진입의 모든 안정 + 인터페이스 + 운영 기반이 완성된다.", { bold: true }));
children.push(p(""));
children.push(p("문서 ID: LOS-V621-V630-PROPOSAL-V3-2026-05-25", { italics: true }));
children.push(p("기반 v2.0: literary_os_v601_v630_phase_b_proposal_v2.docx (commit f16c5c8)", { italics: true }));
children.push(p("V620_R supersedes: literary_os_v620_r_proposal/blueprint.docx (참조 보존, push 안 함)", { italics: true }));
children.push(p("후속 본안 설계도: literary_os_v621_v630_phase_b_blueprint_v3.docx + .md", { italics: true }));
children.push(p("후속 handoff: 2026-05-25_v621_v630_phase_b_main_handoff_v3.md (정상 .md 확장자)", { italics: true }));
children.push(p(""));
children.push(p("Chief Architect       Chief Compiler       Chief System Principal Engineer", { bold: true, align: AlignmentType.CENTER }));
children.push(p("___________          ___________          ___________________________", { align: AlignmentType.CENTER }));
children.push(p(""));
children.push(p("— V621~V630 Proposal v3.0 (Final) | Based on v2.0 commit f16c5c8 + 감사 2026-05-25 | 2026-05-25 —", { align: AlignmentType.CENTER, italics: true }));

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Malgun Gothic", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Malgun Gothic" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Malgun Gothic" },
        paragraph: { spacing: { before: 180, after: 90 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [
      { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
    ] },
  ] },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1080, bottom: 1440, left: 1080 } },
    },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Literary OS — V621~V630 Proposal v3.0", size: 18, font: "Malgun Gothic", italics: true })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " / ", PageNumber.TOTAL_PAGES], size: 18, font: "Malgun Gothic" })] })] }) },
    children: children,
  }],
});

Packer.toBuffer(doc).then(function(buf) {
  fs.writeFileSync('literary_os_v621_v630_phase_b_proposal_v3.docx', buf);
  console.log('OK proposal v3', buf.length);
});
