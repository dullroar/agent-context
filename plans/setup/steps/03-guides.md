---
id: 03-guides
status: done
depends_on: [setup/02-scripts]
touches:
  - docs/**
  - README.md
  - examples/**
lane: guides
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R2, R3, R5, R6, R7]
evidence: "2026-11-08: wrote docs/setup.md, README setup/status links, three copy-paste instruction snippets and an optional session-registry skill template. The skill-creator quick_validate.py passed; Copilot CLI 1.0.107 discovered the template in an isolated project (discovery only). Local Markdown links and Bash examples passed checks; Windows PowerShell parsed its examples. Isolated Bash and Windows PowerShell dry runs passed without creating registry or agent integration files. The guide's disposable shared-root probe passed WSL write/read and Windows read outside the sandbox, then was removed. See execution note below for corrected harness failures and interface limits."
---

# Write human and agent setup guides

## Change

Explain the model, root selection, setup, verify, update, uninstall, troubleshooting and limitations per environment. Include copy-paste instructions for AGENTS.md, CLAUDE.md and supported Copilot equivalents; add a skill template only if research supports it and explain that it is advisory. Show the hooks or wrappers with no implied guarantee beyond observed support.

Give one copy-paste installation command each for Bash and PowerShell, describe
the single registry-location prompt and optional path argument, and explain how
to read the per-agent results and re-run safely after fixing access. Document
that a Windows root and a WSL root are host-specific choices, even when they
refer to the same underlying directory.

Show the user-profile-based Windows and WSL examples from the plan protocol,
including how to verify their shared location. Explain interop requirements
and keep the prompt and arbitrary registry-root selection available.

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

## Execution note — 2026-11-08

After the WSL acceptance checks, the README, setup guide, adoption matrix and
setup-results handoff were updated to distinguish the authenticated sessions
and observed VS Code hooks from earlier loopback-only tests. Local Markdown
links and `git diff --check` passed after that update. Desktop, VM, remote sync
and unverified interfaces remain explicitly limited in the linked acceptance
record.

The guide identifies host-specific launcher paths, the one-question setup,
unattended root argument, inspection, dry-run limits, update, teardown,
troubleshooting, manual workflow, and a version/interface matrix. The hook
matrix labels synthetic-provider WSL results separately from authenticated,
Windows-native, IDE and desktop acceptance. It does not claim automatic
registration, instruction following, or resume. A skill template is included
because research observed skill discovery; invocation is not assumed.

The first isolated Windows dry-run harness did not find `powershell.exe`
because the test PATH omitted its directory. A second harness incorrectly
treated empty `profile/AppData` directories created by the host processes as
agent-configuration changes. Those disposable files were inspected and
removed. With the corrected PATH and checks for the registry, integration,
and agent-config locations, the documented PowerShell dry run passed. This
is a dry-run check, not an authenticated agent or UI acceptance result.
