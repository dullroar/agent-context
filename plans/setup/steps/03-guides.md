---
id: 03-guides
status: pending
depends_on: [setup/02-scripts]
touches:
  - docs/**
  - README.md
  - examples/**
lane: guides
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R2, R3, R5]
evidence: ""
---

# Write human and agent setup guides

## Change

Explain the model, root selection, setup, verify, update, uninstall, troubleshooting and limitations per environment. Include copy-paste instructions for AGENTS.md, CLAUDE.md and supported Copilot equivalents; add a skill template only if research supports it and explain that it is advisory. Show the hooks or wrappers with no implied guarantee beyond observed support.

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
