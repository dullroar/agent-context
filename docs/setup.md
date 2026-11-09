# Setup and operation

The registry stores pointers to native sessions, not transcripts. Its CLI works
offline after installation. The setup scripts configure **CLI launchers** in the
host where they run; they do not configure a VS Code extension, desktop app,
cloud session, another user, or a different operating system.

## Prerequisites and root choice

- Python 3.10 or newer, pip, and PyYAML. Install the CLI from this checkout:
  `python -m pip install .`. Pip may need network access to obtain dependencies;
  after installation registry operations do not need a network or model.
- Bash on Linux/WSL, or Windows PowerShell and Windows Python on Windows. Run
  the command from the repository root. The scripts do not install the agent
  CLIs or PyYAML for you.
- Choose a directory the running host can create, read, write, and delete in.
  The script displays the resolved root and runs a disposable write/read/delete
  probe before changing agent integrations. A failed probe stops setup; no
  alternative root is selected. The root may be created if absent.

The WSL and Windows spellings are separate host-specific choices. They can
refer to the same underlying directory, but verify that rather than assuming
it. An absolute path is a hint, never the portable project identity. Use a
Git remote plus repository-relative path where appropriate; a record does not
require Git.

## Install or inspect

From this checkout, run the command for the host that will launch the agent:

```bash
./scripts/setup.sh
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

A normal run asks one question: **Where does the registry go?** Supply the
path as the sole positional argument for unattended use, for example:

```bash
./scripts/setup.sh "$HOME/agent context registry"
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 (Join-Path $env:USERPROFILE 'agent context registry')
```

Codex, Claude Code, and Copilot are checked independently using bounded version
and help probes. An executable on PATH does not establish authentication,
policy, or support in another UI. Results distinguish an installed wrapper,
absent command, unsupported shim, failed probe or installation, and manual
steps. A per-agent failure does not stop the other checks. Fix the reported
problem and rerun; an existing modified managed file is a conflict, not an
invitation to overwrite it. The Windows VS Code Copilot shim is reported as
unsupported until its standalone CLI behavior is verified.

Inspect, preview, or remove managed integration files with the same entry
point and one of these flags:

```bash
./scripts/setup.sh --inspect
./scripts/setup.sh --dry-run "$HOME/agent context registry"
./scripts/setup.sh --uninstall
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 --inspect
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 --dry-run (Join-Path $env:USERPROFILE 'agent context registry')
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 --uninstall
```

Dry-run does not probe the root or check every file conflict. Inspect verifies
managed files; it does not prove authentication, hook trust, instruction
following, or another interface's behavior. Teardown removes only unchanged
managed files and leaves registry records intact. If you changed a managed
file, inspect the reported conflict and reconcile it before retrying. Keep the
same `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `COPILOT_HOME`, and
`AGENT_CONTEXT_SETUP_HOME` settings for setup, inspection, and teardown.

To update managed artifacts, first inspect and uninstall the previous version,
then run setup from the updated checkout with the desired root. If teardown
reports a modification, preserve or reconcile that change before retrying.
Do not delete the registry as part of an update.

## Launch and verify

On WSL/Linux, setup normally places launchers in
`~/.local/share/agent-context/integrations/<agent>/<agent>`. For example:

```bash
"$HOME/.local/share/agent-context/integrations/codex/codex"
"$HOME/.local/share/agent-context/integrations/claude/claude"
"$HOME/.local/share/agent-context/integrations/copilot/copilot"
```

On Windows, use the path reported by setup. With `LOCALAPPDATA` set, a Codex
launcher can be started from PowerShell as follows; substitute `claude` or
`copilot` for both occurrences as needed:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $env:LOCALAPPDATA 'agent-context\integrations\codex\codex.ps1')
```

If `LOCALAPPDATA` is unset, setup uses the user home instead. The optional
`AGENT_CONTEXT_SETUP_HOME` changes the managed integration location; use the
reported paths when it is set. These launchers set `AGENT_CONTEXT_HOME` for
that process and its children. For a separate terminal, set the root explicitly
before invoking the registry CLI:

```bash
export AGENT_CONTEXT_HOME="$HOME/agent context registry"
agent-context search 'topic'
agent-context validate
```

```powershell
$env:AGENT_CONTEXT_HOME = Join-Path $env:USERPROFILE 'agent context registry'
agent-context search 'topic'
agent-context validate
```

Each CLI command displays its resolved root. A warning about unavailable
records means a search or validation may be incomplete even if its exit code
is zero. See the [CLI contract](../specs/0001-filesystem-session-registry.md#reference-cli-contract).

### Interface matrix

| Host and interface | Setup behavior | Evidence and limits |
| --- | --- | --- |
| WSL CLI: Codex 0.157.0, Claude Code 2.1.319, Copilot CLI 1.0.107 | Managed launcher, start-hook guidance, and per-launch monitor. | Synthetic loopback and authenticated sessions observed start events and native IDs; missing-root turns continued with warnings. Codex requires hook review/trust; policy may disable hooks. |
| Other Linux/WSL versions | Launcher and guidance; hook integration reported unverified. | Version detection is not proof of supported events or authentication. |
| Windows CLI | PowerShell launcher and guidance; hook integration reported unverified. | Disposable Windows Claude and bundled Codex backend sessions and cross-host record visibility were tested. The Codex backend was not on PATH; the VS Code Copilot shim returned 127 because a standalone Copilot CLI was not found. |
| VS Code, desktop, remote/cloud | Manual configuration for that execution host. | Project-scoped Claude and Codex hooks were observed in VS Code WSL; a terminal wrapper does not configure them. Other targets and failure modes need independent checks. |

The [WSL acceptance record](../plans/wsl-test/results.md) distinguishes actual
sessions, manual hooks, local mock tests and untested desktop, VM and sync
behavior. A successful test for one version or interface is not a guarantee
for another.

The managed WSL start hook supplies advisory context with an observed opaque
session ID encoded as UTF-8 base64, the event, agent, and runtime. It does not
create a record or infer a title, portable project identity, session end, or
resumability. The monitor reports completion, an unconfirmed start, or a
marked hook failure/timeout; it cannot report if the entire launcher is killed.
Warnings must not deny normal agent work. If hook trust, policy, the selected
host, an explicit caller configuration, or the root prevents the integration,
use the manual workflow below. A Codex user can inspect and review hooks with
`/hooks`; do not bypass trust or workplace policy to make a test pass.

## Instructions and optional skill

Setup creates user instructions only if the corresponding file does not exist.
It leaves existing files unchanged and reports a manual step. Review the
managed `instructions.md` next to the launcher, and add suitable guidance to
the agent's applicable instructions when appropriate. These examples are
copy-paste starting points:

- [AGENTS.md snippet](../examples/instructions/AGENTS.snippet.md)
- [CLAUDE.md snippet](../examples/instructions/CLAUDE.snippet.md)
- [Copilot instruction snippet](../examples/instructions/copilot.snippet.md)
- [Optional skill template](../examples/skills/session-registry/SKILL.md)

Instructions and skills are advisory; discovery does not prove invocation or
compliance. Copilot CLI instruction and skill discovery were observed in a
disposable WSL project; other hosts and clients must be checked separately. A
skill is an optional procedure, not a replacement for an observed hook.

## Manual workflow

At the start of relevant work, confirm the selected root and search for prior
sessions. When useful work should be recorded, obtain the actual vendor-native
ID and a meaningful title from an observed session or the operator. Supply a
portable project identity; use `unknown` when status is not observed. If an ID
is unavailable, say what is missing rather than inventing one. The CLI has no
update command: do not assume an existing record was updated. Ask the owner to
perform or approve a safe update if needed.

```bash
agent-context search 'loan validation'
agent-context register --producer codex --vendor codex \
  --session 'REPLACE-WITH-OBSERVED-ID' \
  --project 'git:https://example.invalid/team/repo.git' \
  --title 'Loan validation' --status unknown
agent-context validate
```

These values are examples, not evidence that an ID, project, or session exists.
Record only pointers and short notes; do not store prompts, transcripts, or
secrets. A stored ID is not proof of cross-machine resume.

## Shared Windows-profile example

The test base chosen for this project is `ai-dist-mem` under the Windows user
profile. It is a test choice, not a required product location. In Windows:

```powershell
$registry = Join-Path $env:USERPROFILE 'ai-dist-mem'
```

In WSL, Windows interop and the drive mount must both work:

```bash
agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')" &&
  agent_context_win_profile="${agent_context_win_profile%$'\r'}" &&
  test -n "$agent_context_win_profile" &&
  agent_context_wsl_profile="$(wslpath -u "$agent_context_win_profile")" &&
  export AGENT_CONTEXT_HOME="$agent_context_wsl_profile/ai-dist-mem"
```

To verify the two spellings reach the same files, the following creates a
unique disposable child, checks it from both hosts, and removes only that child:

```bash
set -eu
agent_context_probe="$(mktemp -d "$AGENT_CONTEXT_HOME/setup-verify-XXXXXXXX")"
trap 'rm -f "$agent_context_probe/probe.txt"; rmdir "$agent_context_probe"' EXIT
printf 'agent-context shared-root probe\n' > "$agent_context_probe/probe.txt"
test "$(cat "$agent_context_probe/probe.txt")" = 'agent-context shared-root probe'
agent_context_windows_file="$(wslpath -w "$agent_context_probe/probe.txt")"
printf '%s\n' "$agent_context_windows_file" | powershell.exe -NoProfile -NonInteractive -Command '$p = [Console]::In.ReadLine(); if ((Get-Content -LiteralPath $p -Raw).Trim() -ne "agent-context shared-root probe") { exit 1 }; "Windows read passed"'
printf '%s\n' 'WSL write/read passed'
```

The base directory must already exist for this verification. If interop,
mounting, or access fails, report the check untested and fix access; do not
silently choose another root. This test does not prove network-share, RDP,
synchronization, or concurrent-write behavior.

## Troubleshooting

- **Root preflight fails:** check the selected path and its permissions on that
  host. The installer has not changed agent integration files in this case.
- **Agent absent or probe failed:** verify the executable runs in that OS and
  inspect its version and help output. A Windows shim on WSL or a VS Code shim
  is not proof of a working standalone CLI.
- **Hook unconfirmed or untrusted:** use the reported launcher; inspect the
  provider's hook settings and, for Codex, review `/hooks`. Policy may prohibit
  hooks. A manual search and registration remain available.
- **CLI missing or write fails:** install/check the CLI and selected root. The
  agent can continue its work; report the incomplete registry operation.
- **Managed file modified:** inspect the exact file and ownership conflict;
  setup and teardown refuse to silently replace or delete it.
- **Root differs between Windows and WSL:** compare the displayed paths and run
  the shared-root check above. Host-specific paths are not project identity.

For interface-specific acceptance and remaining gaps, see the
[WSL test plan](../plans/wsl-test/spec.md).
