# A2R31 FAILURE DIAGNOSIS BOUNDARY R1

Date: 2026-09-14
Parent experiment: `P07-DATA-A2R31-FULL-NOVELTY-SIGNATURE-REALIZATION-PLANNING-QUALIFICATION`
Parent final verdict: **FAIL 6W/2T/4L**

## Immutable parent boundary

A2R31 is closed and must not be rerun, rescored, relabeled, or repaired under the same preregistration.

Frozen qualification gate remains:
- Treatment wins >= 7/12
- Treatment nonloss >= 10/12
- Treatment losses <= 2/12

Observed:
- Treatment wins = 6
- ties = 2
- Control wins = 4
- Treatment nonloss = 8

## What A2R31 successfully demonstrated

- 12/12 selected Control/Treatment planning pairs were materially distinct.
- Identity leakage = 0.
- Duplicate advisory injection = 0.
- One advisory maximum per plan was enforced.
- Full selected novelty signature reached sequence realization.

Therefore the dominant earlier failure mode — signal collapse before planning — was substantially repaired.

## What may be diagnosed without reopening secret mapping

The sealed blind judgment reasons contain several negative planning patterns. These are valid diagnostic observations regardless of which arm later mapped to Treatment:

1. **Novelty overload / causal overpacking**
   - A plan can combine too many abstract causal/thread signals in one sequence, making the causal action less clear rather than more useful.

2. **Case-irrelevant physical novelty**
   - A physical marker can be structurally valid in the donor data yet unsupported by the fresh case affordances. Example class: injecting an arbitrary fall/impact-type action into a case that only requires equipment verification or responsibility transfer.

3. **Generic lifecycle novelty instead of case-specific playable function**
   - A broad Escalation/Callback/Thread marker may be less useful than a concrete document/action/record operation actually afforded by the case.

4. **Minimal concrete physical action can outperform a richer abstract signature**
   - Some cases prefer a single direct visible action such as STOP / record check / document separation over a denser multi-token novelty signature.

5. **Axis-placement mismatch risk**
   - Even a useful novelty can reduce plan quality if inserted into the wrong sequence function or if the case’s primary pressure belongs to another target axis.

## What is NOT claimed under current runtime hold

Container/Python execution is currently unavailable due repeated `TransportTimeoutError`.

Therefore this document does **not** assert the exact identities of the four Treatment-loss case IDs from the secret mapping. Those IDs must not be guessed from the blind judgments.

When runtime/file-byte access returns, the secret mapping SHA and parent result bytes may be reverified to attach exact loss IDs as a supplemental receipt. That supplemental receipt may not alter the parent verdict or this diagnosis direction.

## Localized repair hypothesis

The remaining failure is best framed as **utility control over transmitted novelty**, not as retrieval failure and not as insufficient signal transmission.

A fresh successor should therefore preserve A2R31’s successful transmission architecture while adding three conservative gates before sequence realization:

1. **Case-Relevance Veto**
   - advisory novelty may be used only if it is directly supported by the fresh case’s declared target axis and case affordances;
   - unrelated novelty triggers ABSTAIN.

2. **Novelty Budget / Minimal Sufficient Signature**
   - do not realize every novel token;
   - select the smallest subset that changes the requested planning function;
   - cap abstract novelty density per modified sequence.

3. **Physical-Affordance / Lifecycle Coherence Veto**
   - physical novelty must correspond to a case-supported object/action affordance;
   - Plant/Payoff novelty must create or resolve a coherent obligation/question/object thread rather than merely add generic escalation vocabulary.

## Preserved positive authorities

- A2R10 rolling research retrieval fuel: PASS.
- canonical A2R26 protected-baseline optional advisory + abstention: PASS 10W/2T/0L.
- DB59 historical benchmark remains protected.
- DB64 is not Production DB.

## Scientific next action

Preregister a completely fresh successor with unseen cases, unchanged full-planning quality thresholds, and outputs=0 until the runtime can physically seal generated artifacts.

Status token:

`A2R31_FAIL_IMMUTABLE__SIGNAL_TRANSMISSION_REPAIRED__UTILITY_CONTROL_DEFECT_LOCALIZED__EXACT_LOSS_ID_MAPPING_REVERIFY_PENDING_RUNTIME`
