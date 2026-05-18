#!/usr/bin/env bash
# tag_lineage.sh — Literary OS V400~V571 버전 계보 annotated 태그 생성
# 사용법: git clone https://github.com/limsanghyuk/literary-os && cd literary-os
#         bash tools/tag_lineage.sh && git push origin --tags
set -e
HEAD=$(git rev-parse HEAD)

t() {
  local tag=$1; local msg=$2
  git rev-parse "$tag" >/dev/null 2>&1 \
    && echo "SKIP: $tag" \
    || { git tag -a "$tag" "$HEAD" -m "$msg"; echo "TAG:  $tag"; }
}

echo "=== Literary OS 버전 계보 태그 생성 (V400~V571) ==="

# Phase 0: Foundation
t "v1.0.0-V400"  "Phase0 V400: LongformEnduranceOrchestrator — 장편 지속 v1.0 (V327~V400 누적)"

# Phase 1: Studio API
t "v2.0.0-V420"  "Phase1 V420: StudioAPI v2 — 14 endpoints + OAuth2.1 + OTel"
t "v2.1.0-V430"  "Phase1 V430: React Dashboard + Docker + i18n + CostLedger — SP1 완료"

# Phase 2: LLM Bridge
t "v3.0.0-V462"  "Phase2 SP1: adapters / retrieval / SLM / evaluation 레이어"
t "v3.1.0-V468"  "Phase2 SP3: GDPR + EUAIAct + PIIScanner + AuditTrailDB"
t "v3.2.0-V474"  "Phase2 SP4: LoRA FineTune + ModelEvalHarness + ProseSpecializer"
t "v3.3.0-V480"  "Phase2 SP5: LoadBalancer(WRR) + BillingEngine + Gate20 ScaleGate"
t "v3.4.0-V481"  "Phase2 V481: Hotfix — OTel tracer + TaskRouter + live_core_manifest"
t "v3.5.0-V485"  "Phase2 V485: DramaEpisodeGenerator + SceneGenerationPipeline"
t "v3.6.0-V491"  "Phase2 SP2: RAGPipelineOrchestrator + Gate23 — RAG 완전 통합"

# Phase 3: NIE v2.0
t "v4.0.0-V497"  "Phase3 SP3: TraceQualityFilter + PIIScrubber + SyntheticAugmentor"
t "v4.1.0-V510"  "Phase3 NIE: CIM + QueryIntentClassifier + DramaLexicon"
t "v4.2.0-V518"  "Phase3 NIE: NILStabilityModule + MetaLearner + TIdealLearner"
t "v4.3.0-V525"  "Phase3 V525: NIE v2.0 통합 릴리즈 — 수학적 서사 엔진 완성"

# Phase 4: GIG
t "v5.0.0-V530"  "Phase4 GIG SP1: NarrativeGraph + NarrativeImpactAnalyzer"
t "v5.1.0-V535"  "Phase4 GIG SP2: CodeDependencyGraph + PlanBuildProtocol + Gate26/27"
t "v5.2.0-V540"  "Phase4 V540: GIG 통합 릴리즈 — Graph Intelligence Gate"

# Phase 5: ASD
t "v6.0.0-V545"  "Phase5 V545: StoryDoctorOrchestrator + AutoRepairExecutor + Gate28"

# Phase 6: Cleanup → PNE → Corpus → MultiWork
t "v7.0.0-V546"  "Phase6 StageA: ADR-027~031 + GraphSync + LLM0StaticChecker (Cleanup)"
t "v7.1.0-V555"  "Phase6 StageB PNE: PNECore + DebtPredictor + PreemptiveGate + Gate29"
t "v7.2.0-V561"  "Phase6 StageB+ Corpus: ExternalCorpusBridge + BGE-M3 + Gate30"
t "v7.7.1-V571"  "Phase6 StageC MultiWork: MultiWorkOrchestrator + AuthorLicenseAPI + Gate31 [CURRENT]"

echo ""
echo "=== 생성된 태그 목록 ===" && git tag --list "v*" | sort -V
echo ""
echo "원격 푸시: git push origin --tags"
