# Setup adoption design

## Evidence and scope

This design uses the dated observations and primary sources in
[RESEARCH.md](../../RESEARCH.md), especially its Copilot and Claude/Codex
sections. A documented hook is not evidence that the installed version or a
particular UI executes it. A `--version` probe only establishes that a command
can start and identify itself; it does not establish authentication, policy,
hook support, or an interface's execution host.

| Interface | Observed or documented input/event | Setup disposition |
| --- | --- | --- |
| Copilot CLI 1.0.107 in WSL | `sessionStart` and `sessionEnd` with `sessionId` were observed with a local mock provider; authenticated `sessionStart` and ID were later verified. | The wrapper carries the root and monitors a start hook. Setup adds a separate user hook file only when its managed name is free. |
| Claude Code CLI 2.1.319 in WSL | `SessionStart` and `SessionEnd` with `session_id` were observed with a local mock provider; authenticated `SessionStart` and ID were later verified. | The wrapper supplies additive per-launch settings and monitors a start hook. |
| Codex CLI 0.157.0 in WSL | `SessionStart` and `SessionEnd` with `session_id` were observed with a local mock provider; authenticated `SessionStart` and ID were later verified. Non-managed hooks require trust. | The wrapper supplies per-launch hook configuration and a monitor; the user must review/trust the hook. |
| Windows CLI for each vendor | Windows Claude Code 2.1.317 and the desktop-bundled Codex backend 0.167.0-alpha.3.2 ran authenticated synthetic sessions through disposable wrappers. The Codex backend was not on PATH. A VS Code Copilot shim returned 127 and reported no standalone CLI. | Configure only a host-native working CLI; report missing or unverified support. Windows hook integration remains unverified. |
| VS Code, desktop, remote and cloud | Project-scoped Claude and Codex `SessionStart` hooks were observed in VS Code WSL; the selected harness and execution host vary. | A terminal wrapper does not configure these interfaces. Provide manual instructions and test each available interface separately. |

On 2026-11-08, each installed WSL CLI emitted a start and an end event with a
session ID present during a synthetic turn against a loopback-only mock
provider. Provider-specific start-hook context reached the fake request; these
checks did not exercise authenticated vendor services or non-CLI interfaces.
The installed hook and the observed failure/status limits are recorded in
[the scripts step](steps/02-scripts.md#isolated-mock-provider-hook-work--2026-11-08).
Subsequent authenticated and cross-interface checks, including their limits,
are recorded in [WSL acceptance results](../wsl-test/results.md).

`Stop` or Copilot `agentStop` is an end-of-turn observation, not session end.
Even `SessionEnd` may be missed on interruption. No tested event supplies a
reliable subject and portable project identity for an automatic record. Do not
invent them, a native ID, a lifecycle transition, or a resume capability.
Use `unknown` when the state cannot be observed. Never save raw hook input,
prompts, transcript contents, or secrets. A tested hook must have an explicit
short timeout, catch errors, never deny a tool call,
emit only event-appropriate output, and have host/provider-specific failure,
timeout, and JSON behavior verified before claiming support.

## Layered use

1. A host-specific CLI wrapper sets `AGENT_CONTEXT_HOME` for the launched
   process and its children and forwards arguments and the agent's exit code.
   It emits a short reminder without running a model or requiring a registry
   write. Run the wrapper explicitly unless the operator arranges PATH; its
   presence does not prove that another interface uses it.
2. Short, copyable `AGENTS.md`, Claude user rules, and Copilot instructions tell the
   agent to search at the start of relevant work and, when useful work is
   recorded, register a pointer with observed identifiers or explain the manual
   fallback. These are advisory and do not guarantee compliance. Create a
   managed user instruction file only when its name is free; preserve every
   existing file and report a manual merge. Remove a managed file only when its
   entire content remains unchanged.
   These instructions can also load when an agent is launched without its
   wrapper. In that case they must not assume the chosen root was propagated:
   they tell the agent to check `AGENT_CONTEXT_HOME` and ask for the intended
   registry if it is unset or uncertain.
   In a disposable WSL Copilot home on 2026-11-07, `copilot --no-auto-update
   instruction list --json` reported the installed user instructions. This is
   discovery evidence, not proof of instruction following. Other versions and
   surfaces need their own checks.
3. A skill can package the longer workflow when supported, but discovery and
   invocation vary and it is not a substitute for the instructions or a
   verified hook. The research observed Copilot skill discovery, not invocation.

No automatic pointer creation or update is asserted by this design. The CLI
requires an actual session ID, title and portable project identity; if those
are unavailable, tell the operator what is missing. Failures and unavailable
registry CLI leave the agent's normal work available.

## Installer and ownership contract

Each host has a separate installer, invoking Bash on Linux/WSL and PowerShell on
Windows. A normal interactive invocation asks only for the registry location;
an explicit path supports unattended use. Resolve and show the root, create it
if necessary, then exclusively create a uniquely named probe, write and read
known bytes, and remove only that probe. A failed preflight must precede and
prevent every agent configuration change. No fallback root is permitted.
Inspection, dry-run and teardown are explicit modes and must identify what
would change. Teardown never removes the registry or unrelated files.

After preflight, independently locate and run each of `codex`, `claude`, and
`copilot` with bounded `--version` and `--help` probes. A missing executable is absent; an
error, timeout, or nonfunctional shim is failed, not installed. A CLI executable
on another operating system is not proof of a working local integration.
For each working CLI, install a distinct wrapper and guidance artifact in a
managed, current-user location, using host-correct quoting for both the root and
executable. The wrapper must call the resolved original executable directly,
not rediscover itself on PATH. Tell the operator its exact path and how to use
it. Installing the wrapper configures the wrapper invocation; report other
interfaces as untested or manual, not as installed.

For the tested WSL CLI versions, the wrapper also starts a per-launch hook
monitor. Codex and Claude receive additive hook settings only for that wrapper
invocation; explicit caller-supplied config or settings are preserved, and the
hook is then unconfirmed. Copilot uses an independently owned user hook file;
an occupied name is preserved and reported for manual action. The monitor
reports marked hook failures or timeouts without denying agent work. It cannot
guarantee a report if the entire launcher is killed, and it warns when a hook
event is not confirmed. Hooks must not be claimed for other hosts or versions
without evidence.

The documented instruction locations are Codex's user `AGENTS.md` (or its
existing override), Claude's user `rules/agent-context.md`, and
Copilot's user `copilot-instructions.md`, respecting the corresponding home
override environment variables. The instructions may be ignored or superseded
by client configuration.

Managed files must be identifiable and independently reversible. Preserve
existing files, hooks and unrelated settings. Compare current content with the
last installed managed content before replacing or deleting; an unexplained
change is a visible conflict, never an overwrite. A rerun may replace only
unchanged managed artifacts. A per-agent failure is reported while other agents
continue, and a retry is safe. Do not mutate the executor's own configuration
for tests; use isolated homes and fake agents. Do not alter workplace policy.

Tests must prove forwarding, quoting and spaces, propagation of the chosen root,
one-question interactive behavior, no-clobber and teardown, all detection
combinations, broken shims, inaccessible roots, probe cleanup, partial failure,
and no agent mutation on preflight failure. The actual Windows and Bash shells
and the shared mount are separate required checks; fake executables demonstrate
installer behavior, not vendor hook support. Then run the full offline CLI suite.

## Shared-root example and limits

The selected test base is `Join-Path $env:USERPROFILE 'ai-dist-mem'` on
Windows, and `$(wslpath -u "$agent_context_win_profile")/ai-dist-mem` in WSL
after obtaining the Windows profile as shown in the
[plan protocol](../README.md#shared-windowswsl-test-location). On 2026-11-07
in this WSL2 environment, an outside-sandbox unique child was written and read
from WSL and read via Windows PowerShell, then the probe and child were removed.
The sandbox mount is read-only and interop failed inside it. This establishes
only the tested access path, not network-share semantics, agent integration,
concurrency, or every environment. Installers must accept any selected root;
these host-specific spellings are not product defaults or project identity.
