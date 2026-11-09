---
id: 01-baseline
status: done
depends_on: [cli/04-integration, setup/04-validate]
touches:
  - plans/wsl-test/results.md
lane: wsl
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R5]
evidence: "2026-11-08 WSL2 Python 3.12.3 / PyYAML 6.0.1 outside the sandbox: the selected Windows-profile ai-dist-mem 9p/DrvFs mount was writable. In a unique disposable child, synthetic register/list/search/show/validate, UTF-8 and spaces, two topics sharing an opaque session, 12 concurrent creates, and a simulated write failure with preservation passed; all 14 valid records remained and the child was removed. Exact commands, root mapping, synthetic project identity and limits are in ../results.md."
---

# Test the CLI on a disposable WSL root

## Change

Record WSL, OS, CLI and filesystem versions. Exercise all commands, same-session topics, search, spaces/UTF-8, concurrent independent creates and simulated failure. Capture commands, results, root and project identity without sensitive content.

Use a unique disposable child under the Windows-profile `ai-dist-mem` WSL
mount as the baseline registry. Record whether the mount is writable in the
actual test environment; a Linux-only temporary directory does not satisfy
this check. Clean up only the files and directory created for this run.

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
