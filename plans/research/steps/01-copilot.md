---
id: 01-copilot
status: done
depends_on: []
touches:
  - RESEARCH.md
lane: research
gate: "manual: compare RESEARCH.md and cited sources to step completion criteria"
requirements: [R1, R5]
evidence: "2026-11-07: reviewed official documentation and retested installed WSL Copilot CLI 1.0.107; instruction and skill discovery and two no-prompt sessionEnd hooks observed in a disposable repo. User reports normal keyring-backed Copilot works; isolated test required login. Authenticated model calls, other events, UI, cloud and enterprise settings untested. See RESEARCH.md for commands and limits."
---

# Investigate GitHub Copilot first

## Change

Compare VS Code session targets (including WSL and remote/cloud), Copilot CLI and desktop/app where available. Record official documentation, versions and local observations for lifecycle events, native IDs, settings/instruction and skill support, execution host, enterprise policy and failure semantics. Distinguish Copilot from Claude/Codex targets. Update RESEARCH.md with sources, dated answers and explicit unknowns.

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
