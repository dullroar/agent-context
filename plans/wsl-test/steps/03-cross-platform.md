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

Run available Windows-native coding agents alongside the WSL agents, all
configured to the selected profile's `ai-dist-mem` base using each host's path.
Verify both directions of visibility and independent records from overlapping
sessions, plus the same Git identity and explicit root selection. Use a unique
disposable child for spaces, long-but-valid paths, concurrent writes and
interrupted-write checks; preserve unrelated data. Record missing Windows agent
access as blocked/untested. Separately, where available and authorized, test
RDP redirected client storage from VM Windows and VM WSL, reconnect behavior,
and an approved alternative. Record the actual storage and observed semantics;
do not assume atomic rename or claim the local Windows mount is an RDP share.

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
