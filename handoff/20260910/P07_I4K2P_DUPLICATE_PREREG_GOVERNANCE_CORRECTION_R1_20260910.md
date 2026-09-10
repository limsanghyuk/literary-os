# P07-I4K-2P Duplicate Preregistration Governance Correction R1

Date: 2026-09-10

A later preregistration was mistakenly created under the already-used experiment id `P07-I4K-2P-SECOND-ORDER-PROPAGATION-REPLICATION` at commit `7e5100e10bf82e7677b7f55fa9b27d9b4ffc78f2`, after the session failed to notice that the original experiment had already executed and closed as a prescore HOLD under prereg commit `b6a21fd77522e42caf549d46f9346c19eb755429`.

Correction status for the later prereg:
`VOID_NO_OUTPUT__DUPLICATE_EXPERIMENT_ID__SUPERSEDED_BY_PRESERVED_ORIGINAL_HOLD_LINEAGE`

No candidate, mask, score, unblind, scientific verdict, engine change, or physical-authority claim was produced from the later duplicate preregistration. It must never be used as an experimental authority or combined with the original I4K-2P outputs.

The authoritative I4K-2P record remains:
- original prereg commit `b6a21fd77522e42caf549d46f9346c19eb755429`;
- prescore HOLD closure `P07_I4K2P_PROPAGATION_REPLICATION_HOLD_CLOSURE_R1_20260910.md`;
- physical Research Sync R7 material SHA256 `faf07340e780786978e91a8a389223a4805ec2f1546b2acb080ebc3610af8f22`.

Any new retry must use a new experiment id and fresh synthetic world/candidates, and must prospectively prevent treatment verbosity using field-level budgets before generation.