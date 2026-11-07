---
id: 01-adoption-design
status: pending
depends_on: [archive/research/02-agent-hooks, archive/research/03-shared-storage, archive/research/05-decisions, cli/01-contract-fixtures]
touches:
  - plans/setup/adoption.md
lane: design
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R2, R3, R4, R6, R7]
evidence: ""
---

# Design integration and adoption layers

## Change

Write adoption.md with a vendor/interface matrix, exact observed events and IDs, setup/teardown proposal, hook-versus-instructions-versus-skill rationale, no-clobber behavior, failure-open semantics and manual fallback. Explicitly capture unavailable enforcement and storage-root decisions; use documented research rather than guessing capabilities.

Specify the Bash and PowerShell one-command flows: detect Codex, Claude Code
and Copilot separately; ask only for the registry root; verify that root before
installing anything into agents; then map each supported integration to its
own artifact and host-specific destination. Define a safe way to carry the
selected `AGENT_CONTEXT_HOME` into each agent's hook or wrapper and report
any host where this cannot be established. Account for Windows versus WSL,
shims, unsupported interfaces, existing settings, safe reruns and partial errors.

Use the Windows-profile `ai-dist-mem` test base defined in the plan protocol
for the adoption and test examples, with different host-specific path spellings
and one verified shared location. Keep the installer's root choice configurable.

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
