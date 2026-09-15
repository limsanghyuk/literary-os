# Literary OS Experiment Record Schema R1

새 세션은 실험 결과 숫자만 읽어서는 안 된다. 각 실험은 왜 생겼고, 무엇을 바꾸었으며, 실패가 다음 실험에 어떻게 전달되었는지를 복원할 수 있어야 한다.

## Mandatory fields(필수 항목)
1. `experiment_id`
2. `date`
3. `parent_authority`
4. `maturity_gate`
5. `status`
6. `purpose`
7. `hypothesis`
8. `research_question`
9. `predecessor_problem`
10. `frozen_inputs` + SHA256
11. `implementation_freeze`
12. `control_treatment_or_reference`
13. `evaluation_rules`
14. `pass_fail_gate`
15. `execution_log`
16. `infrastructure_incidents`
17. `raw_outputs`
18. `mapping_and_blindness`
19. `judge_receipts`
20. `result`
21. `critical_adjudications`
22. `claim_boundary`
23. `what_changed_from_parent`
24. `what_did_not_change`
25. `successor_recommendation`
26. `physical_reseal`
27. `hub_custody`
28. `artifact_manifest`

## Preservation doctrine(보존 원칙)
- FAIL은 지우지 않는다.
- SUPERSEDED/ABORTED/NOT_SCORED도 계보에 남긴다.
- 같은 preregistration을 결과 후 다시 실행한 duplicate branch(중복 분기)는 정본에서 격리한다.
- Infrastructure Failure(인프라 실패)는 Scientific Failure(과학 실패)와 분리한다.
- 결과 이후 threshold/input/mapping을 바꾸지 않는다.
- 새 연구가 권위를 바꾸면 5-Part/9-Package에 편입하고 reseal(재봉인)한다.
- 새 세션은 `CURRENT_SESSION_RECOVERY_POINTER → START_HERE → RESEARCH_EVOLUTION_MAP → LEVEL3_ENTRY_GATE_LEDGER → 개별 Experiment Record` 순서로 읽는다.
