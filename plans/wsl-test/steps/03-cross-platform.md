---
id: 03-cross-platform
status: pending
depends_on: [wsl-test/02-claude-codex]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R3, R5]
evidence: ""
---

# Exercise Windows, VM and shared-root behavior

## Change

Where authorized and available, use a disposable root to test the same Git identity from Windows and WSL, explicit root selection, spaces, long-but-valid paths, independent concurrent writes, interruption and reconnect. Test RDP redirected client storage from VM Windows and VM WSL separately, and an approved alternative if available. Record exact storage and observed semantics; do not assume atomic rename.

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
