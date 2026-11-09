---
id: 02-scripts
status: done
depends_on: [setup/01-adoption-design, cli/03-command-line]
touches:
  - scripts/**
  - tests/test_setup*
lane: scripts
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R1, R3, R4, R5, R6, R7]
evidence: "2026-11-08: WSL installers and monitored start hooks for the three explicitly version-gated CLIs passed isolated local and shared-root end-to-end tests with synthetic providers, including existing hooks, actual session IDs, forced hook interruption, timeout, missing root, rerun and teardown. Shared-root WSL installer controls passed 20 tests; Windows PowerShell installer controls passed 7 and Windows hook-unit controls passed 9. The local offline suite ran 75 tests with 15 platform/opt-in skips. Authenticated services, Windows-native hooks, IDEs and desktop modes remain unverified and are not claimed; see execution record below."
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

## Execution record — 2026-11-07

WSL2 Ubuntu, Python 3.12.3, Windows PowerShell 5.1 and Windows Python 3.14.4.
The branch initially had a clean working tree. No personal agent configuration
was modified and no model prompt was submitted. Setup scripts, launchers and
tests are **in progress**, not an accepted installer.

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` ran 37 tests: 29
  passed and 8 platform-specific cases were skipped. This is a local control,
  not a pass for the skipped Windows or mounted-reader checks.
- `AGENT_CONTEXT_TEST_PARENT="$agent_context_parent" PYTHONPATH=src python3
  -m unittest discover -s tests -p 'test_setup.py' -v`, with a unique child of
  the Windows-profile `ai-dist-mem` WSL mount as the parent, passed 12 tests.
- With `AGENT_CONTEXT_TEST_PARENT` pointing to another unique child of the
  same base and `WSLENV=AGENT_CONTEXT_TEST_PARENT/p`, Windows Python ran
  `-m unittest discover -s <Windows spelling of tests> -p
  test_setup_windows.py -v`: 5 tests passed using Windows PowerShell. They
  cover all agent-presence combinations, a broken shim, preflight ordering,
  reruns, user modifications, teardown, the prompt, and a spaced Unicode path.
  Both mounted test parents were removed after their test-created children.
- Disposable WSL homes were used to run the generated wrappers with the
  installed Codex 0.157.0, Claude Code 2.1.319 and Copilot CLI 1.0.107 using
  only `--version`. Copilot's `instruction list --json` separately discovered
  the installed user instruction in an isolated home. Neither check proves
  authentication, instruction following, agent hook behavior, or other UIs.
- An isolated no-prompt Copilot session with an independent user-level
  `sessionEnd` probe invoked the hook; the earlier research separately observed
  IDs in two such events. A proposed progress reminder was not visibly surfaced
  at exit, so it was not installed. Isolated
  no-prompt Codex and Claude launches reached sign-in before a `SessionStart`
  hook was observed. Claude initially encountered the sandbox's network/DNS
  restriction; outside the sandbox it reached the login screen. No account
  login, model request, or paid API call was made. All three probes used
  disposable homes; test artifacts were removed.

### Offline follow-up

The shared user-level instructions can load without the CLI wrapper, so they
now require checking `AGENT_CONTEXT_HOME` and asking for the intended registry
when it is unset or uncertain. Failure cleanup now preserves newly created
instruction and wrapper files if their contents changed during setup, and
reports them for inspection. Tests exercise this and a user edit detected
before replacing an existing instruction file. This is not proof that an
uncooperative concurrent editor cannot change a file between the final check
and replacement; that race remains unverified.

On the shared Windows-profile 9p mount, `chmod 0600` did not change the mode
reported to WSL. This does not establish or change the Windows ACL. To avoid
claiming ACL preservation from POSIX mode bits, the installer now declines to
replace existing instructions on Windows or on Linux 9p, drvfs, CIFS and SMB3
mounts, and reports a manual merge. It also declines when the Linux mount table
cannot be read. Existing instructions on the selected 9p mount were preserved
in the subsequent test.

After these changes, `PYTHONPATH=src python3 -m unittest discover -s tests -q`
ran 40 tests locally: 32 passed and 8 platform-specific cases were skipped.
The same mounted WSL setup command listed above ran 15 tests: 14 passed and the
existing-file merge test was skipped because this filesystem deliberately uses
the manual fallback. The Windows setup command listed above passed 5 tests.
Each mounted run used and removed its own disposable child. These results do
not clear the provider hook checks below.

### Real executable and Windows shim follow-up

`AGENT_CONTEXT_SETUP_REAL_AGENTS=1 PYTHONPATH=src python3 -m unittest discover
-s tests -p 'test_setup_real_agents.py' -v` passed locally and with
`AGENT_CONTEXT_TEST_PARENT` set to a unique child of the selected 9p mount.
The test used isolated homes and an environment without personal credentials;
it inspected `/proc/<pid>/environ` for the selected root in the real Codex
0.157.0, Claude Code 2.1.319 and Copilot 1.0.107 `--version` processes. No
prompt or model call was made. This verifies process environment propagation
for those CLI invocations, not instruction following or hook events.

Windows PowerShell, with only Windows Claude and Python on PATH and a disposable
profile and registry beneath the shared base, ran `scripts/setup.ps1`, the
resulting Claude wrapper with `--version`, and `scripts/setup.ps1 --uninstall`.
All returned zero; Claude reported 2.1.317. The test child was removed. This
establishes launcher execution, not the contents of Claude's environment or
authenticated behavior. A separate Windows command-discovery check found a
VS Code `copilot-shim` executable. Because its CLI behavior is unverified, the
installer now reports that known shim as unsupported without executing it. An
isolated run against that actual shim path confirmed the report and did not
install a Copilot wrapper. This does not establish whether the shim could work
in another supported mode.

After the shim check was added, the local suite ran 42 tests: 32 passed and 10
were skipped, including the opt-in real-agent test. The separate Windows setup
suite passed 6 tests in another disposable shared-root child. None of these
checks clears the provider hook requirements below.

### Isolated mock-provider hook work — 2026-11-08

The opt-in suites `tests/test_setup_codex_mock.py`,
`tests/test_setup_claude_mock.py`, and `tests/test_setup_copilot_mock.py` run
the installed WSL CLIs against local synthetic HTTP providers. Each suite was
run locally and in a unique child of the selected shared test base. The runs
used `unshare -Urn`, brought up loopback, checked that `ip -j link show`
contained only `lo`, supplied disposable homes and synthetic credentials, and
removed the test children. The servers record request paths and boolean marker
checks, not request bodies or hook payloads. No external model or paid service
was contacted. For example, the Codex suite was run with:

```bash
unshare -Urn bash -c 'ip link set lo up && AGENT_CONTEXT_CODEX_MOCK=1 PYTHONPATH=src python3 -m unittest discover -s tests -p "test_setup_codex_mock.py" -v'
```

The Claude and Copilot commands substitute `CLAUDE`/`claude` or
`COPILOT`/`copilot`; mounted runs also set `AGENT_CONTEXT_TEST_PARENT` to a
unique child of the Windows-profile `ai-dist-mem` mount. All three suites
passed their nine synthetic scenarios in both locations: documented start/end
events and ID presence, provider-specific context JSON, experimental adapter
guidance, unset and missing roots, supervised worker interruption and timeout,
and direct hook exit 2, timeout and forced termination. The fake providers
received the adapter's guidance or warning context as appropriate; the turn
continued in each scenario. These are WSL CLI harness results, not evidence of
authenticated vendor sessions, Windows-native hooks, IDEs or desktop modes.

In these noninteractive modes, a direct hook timeout or forced termination
completed the synthetic turn without an observable hook warning in captured
CLI output. Copilot did display its synthetic exit-2 warning; Codex JSON and
Claude JSON did not display comparable hook warnings. A supervised worker
failure produced warning context received by each fake provider, but the
supervisor itself can be killed before producing output. Therefore the R4
interrupted-hook warning/status requirement is not proved by these checks.
The experimental `scripts/hook_context.py` is not installed by setup. It has
unit tests for opaque IDs, malformed inputs, root failures and supervised
worker failures; the corresponding Windows Python suite passed six tests in a
disposable shared-root child. Access probes are advisory, not proof of a later
successful write.

The first shared-root Copilot mock run timed out in all four original cases
and initially left test artifacts. Logs showed repeated `gh auth token`
timeouts; those observations do not by themselves establish the sole cause.
The test was changed to use a failing synthetic `gh` shim, a bounded process
group, and fail-fast baseline behavior. The abandoned child was inspected and
removed, and the revised shared-root Copilot suite passed. An intermediate
supervisor test also failed when `systemMessage` was absent from captured
Codex/Claude JSON output; the prototype was changed to provide warning context
as well, and the revised suites passed. Neither failure is counted as a pass.

### Installed integration and monitoring — 2026-11-08

The earlier prototype has since been integrated for the tested WSL versions:
Codex 0.157.0 and Claude Code 2.1.319 receive additive per-launch hook settings;
Copilot CLI 1.0.107 receives a separate managed user hook file when its name is
free. A caller's explicit Codex config or Claude settings are preserved and
cause the integration to remain unconfirmed. Codex requires user hook trust.
Other hosts and versions receive wrappers and manual fallback, not a claim of
verified hooks. Existing instruction files are now always preserved without
rewriting; the operator is told to merge guidance manually. Earlier notes about
automatic instruction-file merging describe superseded work.

`AGENT_CONTEXT_INSTALLED_MOCK=1 PYTHONPATH=src python3 -m unittest discover -s
tests -p 'test_setup_installed_mock.py' -v` ran inside the loopback-only
`unshare -Urn` namespace, both locally and with `AGENT_CONTEXT_TEST_PARENT`
pointing to a unique child of the shared 9p base. Both runs passed. In each,
the actual installed wrappers and start hooks delivered the observed native
session ID and guidance to a synthetic provider while pre-existing user hooks
also ran. The test forcibly killed and separately stalled each installed hook;
the launcher emitted a bounded terminal status and each synthetic turn
completed. A missing registry produced both a terminal warning and agent-visible
warning context without stopping the turn. Rerun and teardown preserved the
pre-existing settings. No personal configuration, external model service or
paid API was used.

The monitor is scoped to the wrapper process and reports an unconfirmed start
if no hook completes. It cannot report after the entire launcher itself is
killed, and access checks do not guarantee future writes. These limitations,
authenticated vendor behavior and non-CLI surfaces remain for the handoff and
WSL acceptance plan; mock results do not establish them.
