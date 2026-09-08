# START HERE — P07-I4G ACTIVE CHECKPOINT R3

Date: 2026-09-08
Classification: SESSION RECOVERY / DEVELOPMENT PREFORMAL

## CURRENT EXACT STATE
`TREATMENT_SEALED__MECHANICAL_GATE_PASS__STAGE_A_NOT_YET_RUN`

Preregistration commit: `dff1c990d72eff1b8f8acf228d856aa212eebe64`.
Sample seal commit: `ae8ec6bc1bb6eb10f5eea96259809e3799a05f54`.
Pre-output gate commit: `c6ad1f137a78fa91868b3871803cb2964e6020f6`.
Treatment/mechanical checkpoint commit: `bb2e50670032b1f9c54ba5685015204ca81d0dde`.

Sample Root SHA256: `ab7a562f9df6e1e99952719039cccc26eaa6ebd8030895d25dde292a22d76f5e`.
PerformanceDirection contracts SHA256: `290090d70ce1df00a2cf03b0f8fe40e590e657dc90d719165cfa77236ccd9bba`.
Treatment bundle SHA256: `f73b093fc7c37fa5dccee805fa2b091588e3cf421fd9c8e69ff9f55bb6d47f15`.
Mechanical gate SHA256: `dc7cb01999ca0ee21f92a80e88d0bd88ae865ac1acb50073c5ae8e64473cbe1d`.

Mechanical gate PASS. Treatment bytes are locked and may not be edited.
Human anchors inspected: FALSE.

## NEXT EXACT ACTION
Create anonymous Stage-A Control-vs-Treatment 12-pair packet, seal mapping separately, write all judgments before mapping reveal, then apply unchanged gate: Treatment wins >=8/12; losses <=3/12; win+tie >=10/12.

If Stage A fails: HOLD, no Stage B, no State Commit, no active promotion; synchronize evidence into cumulative 5/9.
If Stage A passes: only then select fresh DB59 Human Anchors for Stage B.

## ACTIVE ENGINE
Exact P07-I4D remains active. Active C2 SHA256 `1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`.
Current cumulative research authority remains Sync R2 until I4G closes.
