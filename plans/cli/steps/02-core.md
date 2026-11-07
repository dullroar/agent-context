---
id: 02-core
status: pending
depends_on: [cli/01-contract-fixtures]
touches:
  - src/**
  - tests/test_core*
lane: core
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R2, R4, R5]
evidence: ""
---

# Implement deterministic record operations

## Change

Implement root resolution, ID and filename generation, UTF-8 parsing and validation, safe writes, replacement and collision handling. Add meaningful offline tests for each rule, concurrent independent creates and simulated failures; preserve existing valid records.

From this first filesystem implementation step, run the relevant storage tests
against a unique disposable child of the Windows-profile `ai-dist-mem` WSL
mount described in [the plan protocol](../../README.md#shared-windowswsl-test-location),
in addition to local temporary controls. Record each result and report an
unavailable mounted root as blocked; never treat local-only tests as equivalent.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[cli spec](../spec.md) and [execution protocol](../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
