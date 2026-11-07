---
id: 04-validate
status: pending
depends_on: [setup/03-guides, cli/04-integration]
touches:
  - plans/setup/results.md
lane: integration
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R2, R3, R4, R5]
evidence: ""
---

# Validate setup with the CLI and record handoff

## Change

Run setup tests and the complete CLI offline suite after integration. Check no-clobber, repeatability, reversal, missing CLI, write failures, quoting and warning/timeout behavior. Record exact evidence and untested interfaces, and link the WSL test plan.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[setup spec](../spec.md) and [execution protocol](../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
