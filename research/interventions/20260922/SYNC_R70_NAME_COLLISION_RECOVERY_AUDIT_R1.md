# SYNC-R70 Name Collision Recovery Audit R1

Date: 2026-09-22

## Finding

`SYNC_R70_NAME_COLLISION__AUTHORITY_SPLIT`

The label `SYNC-R70` was used for two different physical package hash sets:

### Hub-first SYNC-R70 receipt
- CONTROL: `6217bea7afd3c11eabbe6eb50a641942ce914855a8ea01ad4fb9be524fb63625`
- A: `20fa9be55178417a389f2690770fb29e299822c7bf0c55c47a026a2e036be95e`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2: `c885f3a94d1c1174c968128e8660432a727ff2d2f6d9135811fbf0c436f2b1e4`
- C1: `9beab60c2f215381238a1e8318b220360cc4e826e55ebaded9e4580dd65246a5`
- C2-A: `a6d596153f779c5ea65ead2638a234bcd828078ae0b56e78d40e59fb0a95f067`
- C2-B: `33a9b9d263d22f3696194f13a4ff76829ba99f2ec0e173b4277b262e8626630b`
- D1: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

### Later recoverable local SYNC-R70 second build
- CONTROL: `f2f22a32b23bfe3c58042f3ee2138223ec86a31359a5b1cd763dbaac48e9feca`
- A: `45bf74b581bcf47cce39a1f329ee42598bc109107c8cffce8a797a35ecb74dc7`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2: `667bbb19c09e9ebeaa70d79b53205f1d6bac165827f42868a800813bf2025e2b`
- C1: `dbda0bceec1d4530fc36ca773dec5b32e0707261e7822e557a26eed56cf0e5ac`
- C2-A: `cb909f676d8bbe3f0be8aecc5d2799cdfe5ecc2424316bf1cda37874a05b4a74`
- C2-B: `814daa42b069a24a86e6707ceda502446440fe1fe11d2c7ac25937c0d3255316`
- D1: same as above
- D2: same as above

## Root cause

`PHYSICAL_AUTHORITY_NAME_REUSE_AFTER_LOCAL_REBUILD`

The Hub-first SYNC-R70 receipt was created, then the same local output directory/name was rebuilt later. The local path was overwritten while the Hub retained the first hash set. This created a name/hash split.

This is a physical custody / naming defect, not a scientific mutation of the R72 result.

## Resolution

Do not overwrite or rewrite either SYNC-R70 history.

- Preserve the Hub-first SYNC-R70 receipt as historical evidence.
- Quarantine the later local SYNC-R70 second build as non-current recovery material.
- Create a new uniquely named physical snapshot: **SYNC-R71 Authority Repair**.
- SYNC-R71 changed packages are rebuilt from the currently recoverable validated second-build bytes plus an explicit authority-repair overlay.
- Do **not** claim that changed SYNC-R71 packages are byte-derived from the unavailable Hub-first SYNC-R70 changed-package bytes.

## Scientific state preserved

- R70 F08: Provider validity PASS; formal literary quality HOLD.
- R71 F02: CLOSED PASS.
- R72 F05: CLOSED FAIL because deterministic G9 high-pressure effect gate failed 0/8, required >=6/8.
- R72 blind stage: NOT RUN.
- R73: planned only; fresh preregistration required.

## Runtime/Production/Data boundary

No change to:
- Active Qualified Candidate: R69/R68/R67/R66 lineage
- Active Runtime: exact R69
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64 R127 research-only
- Formal R140: NOT STARTED
- Operational Level-3: suspended / requalification required
