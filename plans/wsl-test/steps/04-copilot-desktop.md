---
id: 04-copilot-desktop
status: done
depends_on: [wsl-test/03-cross-platform]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R4, R5]
evidence: "2026-11-10: WSL Copilot CLI and VS Code WSL Copilot target completed synthetic sessions. The VS Code sessionStart hook supplied an observed native ID; after an initial unset-root warning, a Copilot session registered acr_0ac5b461afa74809ac89cf90a2d16c45 at /mnt/c/Users/jimle/ai-dist-mem. Independent CLI show/search passed. A separate VS Code Copilot session reported a different observed native ID and successfully found the pointer; no record was changed. The operator could not interact with the desktop Codex chat composer; desktop GUI and Windows VS Code Copilot shim remain untested. See ../results.md."
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
