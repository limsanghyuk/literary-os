# EXT6 Phase01 Quality Patch V1.2.1

- Status: **ACTIVE QUALITY CORRECTION**
- Date: 2026-08-02
- Core Stage01~04 schemas changed: **false**
- EXT6 exact record keysets changed: **false**
- Automatic canonical promotion: **false**

## Corrected defects

1. Enforce authority enums exactly: `speaking_status = SPEAKING | NONSPEAKING`; `focality = PRIMARY | SECONDARY | PRESENT_ONLY`.
2. Preserve numeric speaker suffixes such as `포졸1`, `기생2`, and `사공3`; suffix stripping is prohibited.
3. Resolve source files through `SOURCE_TEXT_MANIFEST.package.json` when canonical filenames differ from work IDs.
4. Verify every CastPresence evidence reference against the source line using Unicode/punctuation-normalized comparison.
5. Require truthful coverage ledgers: annotated and empty scenes must partition the episode; unresolved scenes must be disclosed.
6. Require EntityBridge `source_registry_sha` to equal the current EntityRegistry hash.
7. Recompute CharacterLoad exactly from CastPresence, SceneCard, SequenceBlueprint, and EpisodeArc. Stored CharacterLoad is never trusted as its own evidence.
8. `REFERENCED_ONLY` does not contribute to present/focal/speaking load. Focal count uses `PRIMARY` only.
9. Validation tools must run with bytecode generation disabled; `__pycache__` is forbidden in release packages.

## Remediation scope

- 24 EXT6 works / 460 episodes audited.
- 91,333 CastPresence rows source-verified.
- 15 works / 289 episodes had stale CharacterLoad and were rederived.
- 22,428 mismatched CharacterLoad fields corrected.
- 212 stale or missing CharacterLoad entity rows removed/added by exact rederivation.
- 7,517 `NON_SPEAKING` values normalized to `NONSPEAKING`.
- 1,364 `NONE` focality values normalized to `PRESENT_ONLY`.
- 112 stale EntityBridge registry hashes synchronized.
- 《돌아온 일지매》 numeric-speaker omissions and EP21 terminal alignment repaired.

This patch changes derived/sidecar records only. Existing Stage01~04 authored records remain byte-identical.
