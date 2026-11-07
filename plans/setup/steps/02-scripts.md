---
id: 02-scripts
status: pending
depends_on: [setup/01-adoption-design, cli/03-command-line]
touches:
  - scripts/**
  - tests/test_setup*
lane: scripts
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R3, R4, R5, R6, R7]
evidence: ""
---

# Build one-command Bash and PowerShell installers and agent integrations

## Change

Implement `scripts/setup.sh` and `scripts/setup.ps1`, plus the agent-specific
hook, wrapper or instruction artifacts justified by the adoption design. Each
installer performs this sequence:

1. Ask only where the registry should live, unless the path was supplied as an
   argument. Resolve and show it; safely create it if necessary, then use a
   unique disposable file to verify write, read and cleanup access. Stop before
   changing any agent configuration if that check fails.
2. Detect Codex, Claude Code and Copilot separately in the current host, and
   distinguish an actually runnable CLI from a shim or inaccessible binary.
3. Copy/install the correct distinct artifacts and merge the appropriate
   configuration for each detected, supported agent. Pass the chosen root to
   each integration using a verified mechanism; don't assume the same paths,
   hooks or configuration format apply to all three.
4. Report installed, missing, unsupported and failed integrations, any manual
   actions, and how to verify or undo changes. Do not prompt for additional
   installation choices; preserve unrelated hooks and settings and never
   silently overwrite user modifications. Handle partial failure visibly and
   support a safe retry. Include inspection, dry-run and teardown as specified.

Add offline tests for R1 and R3–R7, including all detection combinations,
preflight failures before any agent mutation, path quoting, no-clobber,
repeatability, failure-open behavior, event handling and per-agent errors. Do
not record prompts, transcripts or secrets. Running the installer explicitly
authorizes the documented current-user setup; this step itself must not modify
the executor's personal or workplace configuration just to test it.

Exercise preflight and supported setup flows using a uniquely named disposable
root under the selected Windows-profile mounted test base, plus local controls.
Use mocked or disposable agent settings for installer tests; test the actual
WSL/Windows agent integrations against the chosen base in wsl-test. Verify the
path is configurable and do not bake a username into either installer.

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
