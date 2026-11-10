---
id: 05-close
status: done
depends_on: [wsl-test/04-copilot-desktop]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R2, R3, R4, R5]
evidence: "2026-11-10: final offline suite passed (75 tests, 15 skipped); bash -n scripts/setup.sh and git diff --check passed. The results matrix records passed mounted-root, WSL Claude/Codex, available Windows-agent, and VS Code WSL Copilot checks, plus untested desktop GUI, Windows Copilot shim, VM/RDP, and cross-device sync/convergence. The separate Copilot session lookup passed. Seven individually verified synthetic registry records and the disposable Copilot test project were removed; unrelated registry entries and user configuration were not changed. See ../results.md."
---

# Reconcile acceptance evidence and remaining gaps

## Change

Run the full offline suite and reconcile each requirement with a pass/fail/blocked/not-tested matrix. Record exact checks, supported and unsupported combinations, expected failures, platform limits, and next action for every gap. Escalate missing WSL Claude/Codex or available VS Code acceptance; do not treat untested VM or desktop scenarios as proven.

Report the mounted-root WSL baseline and available Windows-agent concurrency
and visibility checks individually. Escalate a blocked mounted-root or required
available Windows-agent check; retain VM and unavailable desktop results as
untested where the plan permits, never as proven.

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
