# 02. 정확한 스키마 계약

UTF-8 JSON/JSONL을 사용하고 객체는 exact keyset을 지킨다. 임의 키 추가와 구형 키 대체는 금지한다. 모든 ID는 작품 내 유일하고 모든 FK는 실재 ID를 가리킨다.

## SourceLock v4
`work_id, title, source_type, source_files, source_sha256, episode_count, edition_note, locked_at, by`

## EpisodeMeta v3
`work_id, episode_no, scene_count, core_dist, source_lock, by`  
core_dist는 SceneCard.core_primary만 집계한다.

## SceneCard v3
`scene_id, work_id, episode_no, scene_no, location, time, participants, objective, conflict, action, outcome, state_change, core_primary, core_secondary, source_evidence, by`

## SequenceBlueprint v3
`sequence_id, work_id, episode_no, sequence_no, scene_start, scene_end, scene_ids, goal, pressure, progression, turn_type, turn_class, outcome, source_evidence, by`  
scene_ids는 start~end와 일치하고 회차 전체를 연속 타일링한다. turn_type은 마지막 장면 core_primary다.

### turn_class 파생표
- RISE: `GAIN, ADVANCE, VICTORY, ALLIANCE, COMMITMENT, REVELATION_POSITIVE`
- FALL: `LOSS, DEFEAT, THREAT, BETRAYAL, SEPARATION, REVELATION_NEGATIVE`
- TURN: `REVERSAL, DECISION, DISCOVERY, REFRAME, POWER_SHIFT`
- STALL: `SETUP, PRESSURE, CONFLICT, PURSUIT, ESCAPE, RESCUE, REUNION, ROMANCE, RELIEF, DELAY, MAINTENANCE`
새 core는 manifest 버전을 올린 후 사용한다.

## EpisodeArc v3
`episode_arc_id, work_id, episode_no, opening_state, acts, climax, closing_state, core_dist, sequence_ids, source_evidence, by`  
acts exact keys: `act_no, sequence_start, sequence_end, beat, turn, result`. core_dist는 Sequence.turn_type 집계다.

## CharacterArc v3
`character_arc_id, work_id, episode_no, character, start_state, want, pressure, choice, change, end_state, scene_ids, source_evidence, by`

## RelationshipArc v3
`relationship_arc_id, work_id, episode_no, characters, start_state, interaction, shift, end_state, scene_ids, source_evidence, by`; characters는 정확히 2명.

## LocalEdge v3
`edge_id, work_id, cause_episode, cause_scene_ids, effect_episode, effect_scene_ids, relation, rationale, source_evidence, by`

## PayoffCandidate v3
`candidate_id, work_id, setup_episode, setup_scene_ids, setup, expected_payoff, status, source_evidence, by`  
status: `OPEN, REINFORCED, PARTIALLY_PAID, READY_FOR_DISPOSITION`.

## CandidateDispositionLedger v3
파일명 `<work_id>_candidate_disposition_ledger.jsonl`.  
키: `candidate_id, work_id, disposition, resolved_episode, payoff_id, causal_edge_id, rationale, source_evidence, by`.  
disposition: `CONFIRMED_PAYOFF, RECLASSIFIED_LOCAL_CAUSAL, UNPAID_IN_TEXT, INVALID_CANDIDATE`. 모든 후보는 정확히 한 번 등장한다.

## CrossEpisodeCausalEdge v3
`causal_edge_id, work_id, cause_episode, cause_scene_ids, effect_episode, effect_scene_ids, mechanism, consequence, source_evidence, by`

## Payoff v3
`payoff_id, work_id, candidate_id, setup_episode, setup_scene_ids, development_episodes, payoff_episode, payoff_scene_ids, payoff, state_change, source_evidence, by`

## FullSeriesArc v3
최상위: `work_id, title, episode_count, premise, protagonist, antagonist, central_conflict, want_need_gap, macro_turning_points, character_arcs, relationship_arcs, causal_spine, payoff_summary, thematic_question, ending_state, source_evidence, by`.  
protagonist: `name, want, need, arc`; antagonist: `name, force, strategy, arc`; macro turn: `episode, event, role, consequence`.

## WorkState v1
`work_id, authority_version, episode_count, blocks, last_completed_episode, last_completed_stage, open_candidate_ids, unresolved_checks, next_action, updated_at, by`  
block: `block_id, episode_start, episode_end, status, stage01, stage02, stage03, audit`.
