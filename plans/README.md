# Plans and execution protocol

Active and archived plans preserve the v0 session-pointer boundary. Their
`spec.md` files state outcomes and protected checks; numbered steps record work
and verification. Each `goal.md` gives a restartable execution prompt.
Proposal status is not a claim that implementation or integration has been tested.

| Plan | Purpose | Main dependency |
| --- | --- | --- |
| [cli](cli/spec.md) | Foundation CLI and native session launch | Research decisions before affected implementation |
| [setup](setup/spec.md) | Scripts, hooks, instructions and human setup | Research findings and CLI contract |
| [wsl-test](wsl-test/spec.md) | Exercise WSL, VS Code, Claude and Codex | CLI and setup ready |

Completed plan: [research](archive/research/spec.md) — vendor and storage
findings are maintained in [RESEARCH.md](../RESEARCH.md). Its recorded
steps remain prerequisites for the active CLI and setup plans.

## Shared Windows/WSL test location

Jim's chosen test base, beginning with the CLI work, is `ai-dist-mem` under
the Windows user's profile. Refer to it without hardcoding a username:

- Windows PowerShell: `Join-Path $env:USERPROFILE 'ai-dist-mem'`.
- Windows Command Prompt: `%USERPROFILE%\ai-dist-mem`.
- WSL Bash: query the Windows profile and translate it with `wslpath`:

  ```bash
  agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')" &&
    agent_context_win_profile="${agent_context_win_profile%$'\r'}" &&
    test -n "$agent_context_win_profile" &&
    agent_context_wsl_profile="$(wslpath -u "$agent_context_win_profile")" &&
    export AGENT_CONTEXT_HOME="$agent_context_wsl_profile/ai-dist-mem"
  ```

`USERPROFILE` is not automatically available in every WSL shell. Windows
interop and drive mounting can be disabled or restricted; `WSLENV` is an
optional alternative, not a prerequisite. Do not require a checked-in `.env`
file or hardcode a user-specific path. This is the selected **test location**,
not a new product-wide default or project identity. The setup installer still
asks the operator where to put the registry.

On 2026-11-07, this WSL instance resolved the profile path, and an
outside-sandbox disposable probe passed WSL write/read and Windows PowerShell
visibility, then was removed. The sandbox presented the Windows mount as
read-only and could not invoke Windows interop. This is a WSL mount of a
Windows-hosted filesystem, not proof of an RDP share or of remote/network
filesystem semantics. Rename, concurrency and failure behavior remain untested.

From the earliest filesystem-capable CLI and setup tests, run relevant tests
in a unique disposable subdirectory of this test base as well as any ordinary
local temporary controls. For real-agent acceptance, configure available WSL
and Windows agents against the same selected base and use explicitly identified
synthetic test records; verify both paths really reach the same files. Clean up
only test artifacts created by that run. Never delete or overwrite unrelated
registry data. Record filesystem, path mapping, commands and results. If the
mount, interop, access or Windows interface is unavailable, report the relevant
check blocked/untested rather than substituting a Linux-only result or silently
changing the root. Obtain the access required by the environment when appropriate.

## Dependencies and parallel work

Step `depends_on` entries use `plan/step-id`, including across plans. An
archived dependency uses `archive/plan/step-id` and resolves to
`plans/archive/plan/steps/step-id.md`. A step starts only when its listed
prerequisites are done with evidence. Within and
across plans, steps may run concurrently only if neither depends on the other
and their `touches` do not overlap; otherwise serialize. Each step also owns
its own step file for status and evidence, even when it is not listed in
`touches`. Research steps write
the same RESEARCH.md and therefore run serially. Read each step's full text as
well as its metadata: downstream steps can begin as soon as their precise
prerequisites are complete, not necessarily when an entire plan is complete.
Use isolated branches or worktrees if practical, integrate each lane, and run
the applicable combined validation after integration. Shared documentation,
specification decisions, and final integration have a single owner at a time.

The four specs are proposed work, not blanket approval for live paid API calls,
changes to workplace systems or policy, installing extensions, or modifying
personal configuration. Research and local, reversible offline work may proceed
within the task's authorization; seek the relevant authority for the rest.
Do not commit or push unless separately requested. Preserve existing changes.
For each step record command or manual procedure, environment, date, outcome,
and limitations in `evidence`; do not mark a skipped or unavailable check as
passed. A blocked external environment is reported as such, with the remaining
checks visible. Never silently weaken an acceptance check.
