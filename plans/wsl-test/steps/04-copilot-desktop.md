---
id: 04-copilot-desktop
status: pending
depends_on: [wsl-test/03-cross-platform]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R4, R5]
evidence: ""
---

# Test available Copilot and desktop integrations

## Change

Exercise available VS Code Copilot and relevant CLI/desktop modes with synthetic data and permission; compare hooks, fallback and observed paths to research. Record versions, policy restrictions and unsupported or untested modes. Preserve the earlier WSL results.

Use the same selected Windows-profile registry base for available Windows and
WSL Copilot/desktop sessions and verify their records are mutually visible.
Clean up only test-owned records and explicitly mark unavailable hosts or modes.

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
