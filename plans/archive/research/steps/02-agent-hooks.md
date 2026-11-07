---
id: 02-agent-hooks
status: done
depends_on: [archive/research/01-copilot]
touches:
  - RESEARCH.md
lane: research
gate: "manual: compare RESEARCH.md and cited sources to step completion criteria"
requirements: [R2, R5]
evidence: "2026-11-07: reviewed linked Claude and OpenAI hook, settings, desktop and VS Code documentation; recorded vendor/event/surface matrix and local versions in RESEARCH.md. All hooks, desktop, IDE, resume and failure behavior remain untested locally."
---

# Investigate Claude and Codex integration surfaces

## Change

Compare CLI, VS Code WSL and desktop for each vendor; document hooks, session identifiers, lifecycle semantics, pre/post events, setup, failure/timeout behavior, privacy, instructions and skills. Evaluate evidence separately for each version and host. Update RESEARCH.md after each answer and mark unsupported or untested cases.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[research spec](../spec.md) and [execution protocol](../../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
