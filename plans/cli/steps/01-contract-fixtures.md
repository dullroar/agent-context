---
id: 01-contract-fixtures
status: done
depends_on: [archive/research/05-decisions]
touches:
  - specs/0001-filesystem-session-registry.md
  - tests/fixtures/**
  - plans/cli/**
lane: cli
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R4]
evidence: "2026-11-07: Jim selected Python 3 and a simple installable package and allowed common dependencies; spec 0001 freezes the YAML schema, lifecycle and filename rules, PyYAML dependency, and disposable test parent. In WSL2 Python 3.12.3 / PyYAML 6.0.1, a Python yaml.safe_load/json structural check passed for 2 positive record fixtures, 15 negative record fixtures, and 10 filename cases; git diff --check passed. Semantic rejection and mounted-root operations are verified in downstream steps."
---

# Define the CLI contract and representative fixtures

## Change

Freeze schema examples, safe filename grammar and budget, lifecycle vocabulary, positive and negative cases; select language/packaging from the documented decision. Update spec if required; add machine-readable schema only if it adds value. Record test commands once selected.

Design the filesystem fixtures to accept a disposable child of the selected
Windows-profile `ai-dist-mem` WSL mount from the start of core testing, while
also supporting normal local temporary controls and usernames with spaces.

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

## Preliminary test-location access

On 2026-11-07, WSL2 outside the sandbox resolved the Windows profile and ran
the following disposable probe against its existing `ai-dist-mem` directory.
WSL write/read and PowerShell read passed. The trap removed the probe. An
initial attempt failed because of PowerShell argument parsing; the command
below is the corrected, passing attempt. This is only an access probe, not
the required core or CLI filesystem tests.

```bash
set -eu
agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')"
agent_context_win_profile="${agent_context_win_profile%$'\r'}"
test -n "$agent_context_win_profile"
agent_context_base="$(wslpath -u "$agent_context_win_profile")/ai-dist-mem"
test -d "$agent_context_base"
agent_context_probe="$(mktemp -d "$agent_context_base/cli-access-probe-XXXXXXXX")"
trap 'rm -f "$agent_context_probe/probe.txt"; rmdir "$agent_context_probe"' EXIT
printf 'agent-context access probe\n' > "$agent_context_probe/probe.txt"
test "$(cat "$agent_context_probe/probe.txt")" = 'agent-context access probe'
agent_context_windows_file="$(wslpath -w "$agent_context_probe/probe.txt")"
printf '%s\n' "$agent_context_windows_file" | powershell.exe -NoProfile -NonInteractive -Command '$p = [Console]::In.ReadLine(); if ((Get-Content -LiteralPath $p -Raw).Trim() -ne "agent-context access probe") { exit 1 }; "Windows read passed"'
printf 'WSL write/read passed; base: %s\n' "$agent_context_base"
```
