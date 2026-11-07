---
id: 02-scripts
status: pending
depends_on: [setup/01-adoption-design, cli/03-command-line]
touches:
  - scripts/**
  - tests/test_setup*
lane: scripts
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R3, R4, R5]
evidence: ""
---

# Implement inspectable setup and failure-open adapters

## Change

Implement setup and teardown or dry-run for supported environments and safe adapter wrappers. Preserve existing configuration and unrelated hooks; make repeated installation safe; do not modify user globals by default. Add offline tests for configuration, quoting, lifecycle data, failures and timeouts, without recording prompts or secrets.

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
