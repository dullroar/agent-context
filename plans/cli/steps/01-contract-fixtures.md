---
id: 01-contract-fixtures
status: pending
depends_on: [research/05-decisions]
touches:
  - specs/0001-filesystem-session-registry.md
  - tests/fixtures/**
  - plans/cli/**
lane: cli
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R4]
evidence: ""
---

# Define the CLI contract and representative fixtures

## Change

Freeze schema examples, safe filename grammar and budget, lifecycle vocabulary, positive and negative cases; select language/packaging from the documented decision. Update spec if required; add machine-readable schema only if it adds value. Record test commands once selected.

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
