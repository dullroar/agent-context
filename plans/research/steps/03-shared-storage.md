---
id: 03-shared-storage
status: pending
depends_on: [research/02-agent-hooks]
touches:
  - RESEARCH.md
lane: research
gate: "manual: compare RESEARCH.md and cited sources to step completion criteria"
requirements: [R3, R5]
evidence: ""
---

# Assess desktop, WSL and VM shared-root designs

## Change

Map local Windows, WSL, RDP redirected drive, permitted network share and sync-folder topologies, with paths per runtime and environment-neutral project identity. Investigate drive redirection policy and connection scope, WSL reachability, permissions, concurrent independent creates, rename/replace, disconnected writes, sync conflicts, recovery and privacy. Update RESEARCH.md; keep an untested topology explicitly provisional.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[research spec](../spec.md) and [execution protocol](../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
