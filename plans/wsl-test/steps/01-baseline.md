---
id: 01-baseline
status: pending
depends_on: [cli/04-integration, setup/04-validate]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R5]
evidence: ""
---

# Test the CLI on a disposable WSL root

## Change

Record WSL, OS, CLI and filesystem versions. Exercise all commands, same-session topics, search, spaces/UTF-8, concurrent independent creates and simulated failure. Capture commands, results, root and project identity without sensitive content.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[wsl-test spec](../spec.md) and [execution protocol](../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
