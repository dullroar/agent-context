---
id: 02-claude-codex
status: pending
depends_on: [wsl-test/01-baseline]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R2, R5]
evidence: ""
---

# Test Claude and Codex in WSL and VS Code

## Change

Run distinct real sessions in Claude and Codex CLI; test available VS Code WSL session targets independently. Observe supported lifecycle events, native IDs, lookup from another session and failure-open behavior. Resume only by the vendor-supported tested mechanism. Record inaccessible UI or capability as blocked/untested, not passed.

Point the available WSL agents at the selected Windows-profile `ai-dist-mem`
base and mark any created records as synthetic test data. Preserve the records
needed for the Windows-side visibility check, then remove only test-owned data.

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
