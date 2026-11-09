---
id: 03-cross-platform
status: done
depends_on: [wsl-test/02-claude-codex]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R3, R5]
evidence: "2026-11-08: isolated Windows Claude 2.1.317 and WSL Codex 0.157.0 synthetic sessions overlapped; while both remained active, independent Windows and WSL registry processes created pointers with observed native session IDs. Both host CLIs found both records, using the same Git-origin identity and distinct path hints. On a disposable shared-root child, 8 Windows and 8 WSL concurrent writers produced unique records; writers killed at a controlled pre-publish barrier preserved all 17 final records, validated by both hosts, with a longest Windows path of 197 characters. The operator approved a consumer OneDrive comparison: Windows and WSL both saw both synthetic records locally; documented conflict risks were compared with controlled local duplicate handling. Cloud convergence and cross-device conflicts were not verified. The operator reported VM/RDP unavailable here and plans a separate work follow-up; VM Windows, VM WSL and reconnect behavior remain explicitly untested. See ../results.md."
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
