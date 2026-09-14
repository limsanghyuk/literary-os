# A2R32 RUNTIME HOLD RECEIPT R1

Date: 2026-09-14
Experiment: `P07-DATA-A2R32-UTILITY-CONTROLLED-MINIMAL-NOVELTY-PLANNING-QUALIFICATION`

## Observed execution failure

Repeated minimal execution attempts returned:

`TransportTimeoutError`

Affected execution layers:
- container execution
- Python execution

A minimal `/bin/true` command also failed, so this is treated as an execution-transport failure rather than a scientific output failure.

## Scientific state at hold

- fresh 24-case pool: frozen in Git commit `84aee3ecf641ab2ec3ea94e03f591d28797b9bee`
- preregistration: frozen in Git commit `5d41262255dce76d81b3a30f7ae50ee626d58597`
- retrieval outputs: 0
- planning outputs: 0
- secret mapping: NOT_CREATED
- blind packet: NOT_CREATED
- blind judgment: NOT_CREATED
- PASS/FAIL result: NOT_CREATED

## Required recovery

Before any scientific output:
1. minimal runtime command must PASS;
2. compute SHA256 of fresh pool and preregistration bytes;
3. byte-reverify frozen parent components;
4. freeze and SHA256 the A2R32 implementation;
5. then begin retrieval/planning outputs.

## Fail-closed rule

This hold is not a FAIL and not a PASS.

It is:

`PREREGISTERED__OUTPUTS_0__RUNTIME_HOLD`

Do not reconstruct outputs or mappings from memory.
