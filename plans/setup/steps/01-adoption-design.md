---
id: 01-adoption-design
status: pending
depends_on: [research/02-agent-hooks, research/03-shared-storage, research/05-decisions, cli/01-contract-fixtures]
touches:
  - plans/setup/adoption.md
lane: design
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R2, R3, R4]
evidence: ""
---

# Design integration and adoption layers

## Change

Write adoption.md with a vendor/interface matrix, exact observed events and IDs, setup/teardown proposal, hook-versus-instructions-versus-skill rationale, no-clobber behavior, failure-open semantics and manual fallback. Explicitly capture unavailable enforcement and storage-root decisions; use documented research rather than guessing capabilities.

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
