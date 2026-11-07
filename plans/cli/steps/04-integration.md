---
id: 04-integration
status: done
depends_on: [cli/03-command-line]
touches:
  - plans/cli/results.md
lane: integration
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R2, R3, R4, R5]
evidence: "2026-11-07: full offline suite passed 14 tests in WSL2 Python 3.12.3 / PyYAML 6.0.1 both locally and in a unique disposable child of the selected Windows-profile ai-dist-mem mount outside the sandbox; the mounted child was removed. Offline installation and installed register/validate also passed with dependencies preinstalled; git diff --check passed. Exact commands, requirement coverage and deferred Windows-native, cross-interface and network-filesystem checks are recorded in ../results.md."
---

# Run the complete offline acceptance suite

## Change

Run all protected checks and the full offline suite with no model, daemon or service. Record actual commands, outcomes and platform in results.md. Confirm schema/filename/search tests, failures and distinct topic records; list cross-platform tests deferred to wsl-test.

Include the mounted Windows-profile test base in the integrated storage and
CLI acceptance checks. Preserve independent local controls and report a blocked
mount explicitly. Cross-interface Windows and WSL agent checks remain in wsl-test.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[cli spec](../spec.md) and [execution protocol](../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
