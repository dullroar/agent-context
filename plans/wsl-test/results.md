# WSL acceptance results

The available acceptance checks are complete. The mounted-root WSL baseline,
WSL Claude/Codex and VS Code targets, available Windows-agent overlap, and
VS Code WSL Copilot target passed. The desktop GUI, Windows VS Code Copilot
shim, VM/RDP, and cross-device sync convergence/conflict behavior remain
untested and are not claimed as passes. Final offline validation passed with 75
tests run and 15 skipped. The setup integration's isolated mock-provider
results are recorded separately in [setup results](../setup/results.md).

## Handoff checkpoint — 2026-11-08

The operator stopped this run for the night and requested a commit and push as
an in-progress marker. **The overall setup/WSL acceptance goal is not complete.**
All setup steps and WSL steps 01–03 are marked done for their applicable checks;
WSL step 04 (Copilot/desktop) and step 05 (final reconciliation) remain pending.
Step 03's unavailable VM/RDP and unverified cross-device sync cases were not
passed: the operator plans to investigate VM/RDP from work separately.
For this checkpoint, `PYTHONPATH=src python3 -m unittest discover -s tests`
ran 75 tests successfully with 15 skipped; `bash -n scripts/setup.sh`, local
documentation-link checks and `git diff --check` also passed. These checks do
not replace the pending environment acceptance work.

Next actions for a continuing agent:

1. Read [the execution protocol](../README.md), the [WSL spec](spec.md), and
   the pending [Copilot/desktop step](steps/04-copilot-desktop.md). A WSL
   Copilot CLI start hook and missing-root warning were observed, but the VS
   Code **Copilot** session target and the desktop GUI are not accepted yet.
   An earlier user-run VS Code **Local** target is a different harness and
   did not supply hook context; do not count it as a Copilot-target pass.
2. The operator was given a Windows-native desktop prompt using an empty
   Windows temporary project and the shared registry. Its response is still
   pending. The Windows desktop CLI backend passed separately, but that is not
   proof of desktop GUI behavior. The operator reported their machine was busy
   during a local-model VS Code check; coordinate further interactive tests.
3. For the separate work-side VM/RDP test, confirm the actual remote session,
   client username, policy and authority before moving any data across the
   boundary. Only when permitted, use a unique synthetic child of the approved
   `\\tsclient\C\Users\<username>\ai-dist-mem` location; test VM
   Windows and VM WSL visibility, interruption and reconnect as the spec
   requires. Do not assume `C:` in the VM is the redirected client drive, and
   do not treat the local Windows/WSL 9p results as RDP evidence. The observed
   OneDrive test established local two-host visibility only; cloud convergence
   and cross-device conflict behavior remain untested.
4. The six exact synthetic pointers retained on the selected shared base have
   IDs `acr_1f830d0d059848a284c6ae55883c10de`,
   `acr_911b650b05af4102abfad1c1318d99b7`,
   `acr_70f73760d0cf457d800d1506d1374bd3`,
   `acr_d3ae932d81c94df09f3fcf63dfc249a5`,
   `acr_d801af25851b4f5587084151ac8f1473`, and
   `acr_20129920fd5946d8b379bb34f1ecb103`. Preserve them while needed for
   pending interface lookups; afterwards verify their IDs and synthetic content
   before removing only those files. Do not delete unrelated registry data.
5. Disposable WSL projects under `/tmp/agent-context-vscode-acceptance-9li94vgp`
   and `/tmp/agent-context-vscode-failure-xz6c_u5q`, and a Windows desktop test
   directory under the user's temporary directory, may disappear on restart.
   The two WSL projects have test-specific project and hook trust entries in
   the user's Codex profile, and VS Code workspace-trust entries may also
   persist. Revoke/remove only those test-specific entries through a supported
   review flow when the projects are no longer needed; preserve all unrelated
   settings. Temporary copied credentials from the completed runs were removed.
6. Finish the pending applicable checks, run the required final offline suite,
   reconcile a pass/fail/blocked/not-tested matrix and remaining risks, then
   clean up only test-owned data and trust. Do not mark an unavailable VM,
   sync, desktop or hook check as passed.

## 2026-11-08 — offline WSL baseline

Environment: WSL2 Linux 6.6.87.2-microsoft-standard-WSL2, Python 3.12.3,
PyYAML 6.0.1. Outside the sandbox, the chosen Windows-profile base resolved to
`/mnt/c/Users/jimle/ai-dist-mem`, mounted read/write as 9p/DrvFs in this run.
The unique child was `wsl-baseline-VRSwlQof/registry with spaces`. The path is
run evidence, not product identity or a default. The only project identity
used was the synthetic `git:https://example.invalid/team/repo`.

The following commands used only synthetic IDs and titles. They passed
`register`, `list`, case-insensitive `search`, `show` and `validate`, including
UTF-8, paths with spaces, two distinct topics for one opaque session, 12
independent concurrent registrations, and a simulated write failure. After
failure, the blocker file and all 14 valid records were preserved. The trap
removed the unique test child; no unrelated registry data was touched.

```bash
set -eu
agent_context_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')"
agent_context_profile="${agent_context_profile%$'\r'}"
test -n "$agent_context_profile"
agent_context_base="$(wslpath -u "$agent_context_profile")/ai-dist-mem"
test -d "$agent_context_base"
agent_context_test="$(mktemp -d "$agent_context_base/wsl-baseline-XXXXXXXX")"
trap 'rm -rf "$agent_context_test"' EXIT
export AGENT_CONTEXT_HOME="$agent_context_test/registry with spaces"
export PYTHONPATH="$PWD/src"
printf 'Baseline root: %s\n' "$AGENT_CONTEXT_HOME"
uname -sr
python3 -c 'import sys,yaml; print("Python",sys.version.split()[0],"PyYAML",yaml.__version__)'
findmnt -T "$agent_context_base" -o TARGET,FSTYPE,OPTIONS --noheadings
agent_context_first="$(python3 -m agent_context register --producer codex --vendor codex --session 'synthetic:shared' --project 'git:https://example.invalid/team/repo' --title 'Café verification α' --status unknown)"
agent_context_second="$(python3 -m agent_context register --producer codex --vendor codex --session 'synthetic:shared' --project 'git:https://example.invalid/team/repo' --title 'Second topic' --status unknown)"
agent_context_id="${agent_context_first%%$'\t'*}"
agent_context_id2="${agent_context_second%%$'\t'*}"
test "$agent_context_id" != "$agent_context_id2"
python3 -m agent_context list | rg -F "$agent_context_id" >/dev/null
python3 -m agent_context search 'CAFÉ' | rg -F "$agent_context_id" >/dev/null
python3 -m agent_context show "$agent_context_id" | rg -F 'synthetic:shared' >/dev/null
python3 -m agent_context validate | rg -F '2 valid, 0 invalid' >/dev/null
python3 - <<'PY'
import os, subprocess, sys
cmd=[sys.executable,'-m','agent_context','register','--producer','codex','--vendor','codex','--session','synthetic:concurrent','--project','git:https://example.invalid/team/repo','--title','Concurrent synthetic test']
processes=[subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=os.environ.copy()) for _ in range(12)]
ids=set()
for process in processes:
    out,err=process.communicate(timeout=30)
    if process.returncode:
        raise SystemExit('concurrent register failed: '+err)
    ids.add(out.split('\t',1)[0])
if len(ids)!=12: raise SystemExit('non-unique IDs')
print('12 independent concurrent registrations: passed')
PY
python3 -m agent_context validate | rg -F '14 valid, 0 invalid' >/dev/null
printf 'preserve synthetic blocker\n' > "$agent_context_test/not-a-directory"
if AGENT_CONTEXT_HOME="$agent_context_test/not-a-directory/child" python3 -m agent_context register --producer codex --vendor codex --session 'synthetic:failure' --project 'git:https://example.invalid/team/repo' --title 'Expected failure' >/dev/null 2>&1; then
  printf '%s\n' 'expected write failure did not occur' >&2
  exit 1
fi
test "$(cat "$agent_context_test/not-a-directory")" = 'preserve synthetic blocker'
python3 -m agent_context validate | rg -F '14 valid, 0 invalid' >/dev/null
```

The test ran the module from the checkout with `PYTHONPATH=src`; it did not
validate a fresh installation. It does not prove authenticated agent behavior,
resume, non-CLI interfaces, RDP, or network-share semantics.

## 2026-11-08 — real-session readiness, pending decision

With isolated temporary homes and no model prompt, `--version` reported Codex
0.157.0, Claude Code 2.1.319 and Copilot CLI 1.0.107 in WSL. The VS Code remote
CLI command was present. Directory inspection found WSL extension folders for
Claude Code 2.1.319 and OpenAI's ChatGPT extension; folder presence does not
establish an active VS Code window, an enabled extension, or an available
session target. No real session was started in these readiness checks.

The next step requires distinct real Claude and Codex sessions, lookup from a
separate session, and each available VS Code WSL session target. Those checks,
including authenticated failure behavior, remain **untested**. The earlier
loopback mock-provider results do not substitute for them. The execution
protocol does not treat the plan as blanket authorization for potentially paid
API calls or personal configuration changes; the decision on controlled
authenticated synthetic sessions remains pending. Later Windows-agent,
desktop, RDP and other cross-interface checks have not been started.

## 2026-11-08 — authenticated WSL CLI sessions, partially verified

After the operator authorized up to three synthetic model requests per
available agent, a private temporary home, project, and managed integration
directory were created. Only the existing account credentials and minimal
Claude account/onboarding metadata were copied into that isolated home; those
temporary credential and account-metadata files were removed after the checks.
Setup
was run from this checkout with the shared registry root
`/mnt/c/Users/jimle/ai-dist-mem`; the write/read/delete preflight and setup
returned zero. Personal agent settings were not modified. All session content
was synthetic and no transcript was put in the registry.

The first turn for each agent asked it to report `READY`, the event name and
base64 session ID if present, otherwise `UNKNOWN`; no tools were enabled for
Claude and Codex was launched in read-only sandbox mode. Commands used the
generated launchers from the temporary directory:

```text
<managed>/claude/claude -p <synthetic-prompt> --tools '' --strict-mcp-config --max-turns 1 --output-format json
<managed>/codex/codex exec --skip-git-repo-check --sandbox read-only --json <synthetic-prompt>
```

Both exited zero. Claude reported `SessionStart` and base64
`Mjk1MGQxYTctM2YzNy00NDUzLTkyZjQtYzVhMmQyN2Q2MmM2`; decoding gives
`2950d1a7-3f37-4453-92f4-c5a2d27d62c6`, equal to its native JSON
`session_id`. The monitor reported the start hook completed. Codex reported
native thread ID `01a1bc54-41c0-7bd3-983e-c460acb8c007`, answered
`READY UNKNOWN`, and its monitor reported no confirmed hook; the synthetic
turn still completed. This is an observed untrusted-hook fallback, not a
verified Codex hook event or a resume test.

Two explicitly synthetic records were then created with
`python3 -m agent_context register`, using the observed IDs, status `unknown`,
project `git:https://example.invalid/agent-context/synthetic`, and the unique
tag `acsynthetic20261108stio5b`. Their record IDs are
`acr_1f830d0d059848a284c6ae55883c10de` (Claude) and
`acr_911b650b05af4102abfad1c1318d99b7` (Codex). The records are retained on the
shared root for the planned Windows-side visibility check; remove only these
test-owned records when they are no longer needed.

Separate, new sessions each ran one registry search through their command tool:

```text
python3 -m agent_context search 'acsynthetic20261108stio5b codex'
python3 -m agent_context search 'acsynthetic20261108stio5b claude'
```

Claude found the Codex record and Codex found the Claude record; both commands
and sessions exited zero. Claude's lookup used `--tools Bash`, a narrowly
scoped `--allowedTools` rule, `--max-turns 2`, and stream JSON; Codex used
`exec --skip-git-repo-check --sandbox read-only --json`. The first turns and
two-model-turn lookups use the approved three requests per agent. No additional
model prompt was issued.

In an interactive, prompt-free Codex session in the same disposable home, the
empty test project was trusted and the normal hook review UI showed the
generated SessionStart hook as new. Its command pointed to the copied managed
`hook_context.py`, with a four-second timeout. After reviewing it, trust was
enabled in the disposable profile; the UI showed one installed and one active
SessionStart hook. A new prompt-free session still reported no completed hook
event before exit. It did not establish that a trusted hook runs on a real
model turn or that its ID matches the native thread ID. Additional authorized
model requests are necessary for that check. No trust setting in the user's
personal Codex profile was changed.

`code --status`, run outside the sandbox because its socket was denied inside
it, reported VS Code 1.145.2 connected to WSL Ubuntu. The remote
`code --list-extensions --show-versions` reported
`anthropic.claude-code@2.1.319` and `openai.chatgpt@26.1021.22027`. These
observations establish a running connection and installed extensions, not that
their chat targets are enabled, usable, or correctly configured. There is no
dedicated graphical-control tool in this execution environment. The
authenticated failure cases, VS Code targets, Windows agents, desktop, RDP and
cross-interface checks remain untested. Do not mark this step done.

## 2026-11-08 — trusted Codex hook and real missing-root checks

The operator subsequently authorized up to five additional synthetic requests
per Claude and Codex. In the same isolated home, credentials and minimal
account metadata were temporarily recopied to run the following checks. Copied
credentials, account metadata, and Claude-generated backups of that metadata
were removed afterwards. The earlier test-owned registry records remain for
the Windows-side check.

After the normal review and trust flow recorded above, the installed Codex
wrapper ran another read-only `exec --skip-git-repo-check --json` synthetic
turn against the shared root. The monitor reported a completed SessionStart;
the reply included `SessionStart` and base64
`MDFhMWJjYzAtMTk5ZS03ODAwLThiMDEtMGFjNjExOGMyYzNh`. Decoding that value gives
`01a1bcc0-199e-7800-8b01-0ac6118c2c3a`, equal to the `thread.started` event's
native ID. Exit status was zero. The test did not bypass hook trust.

For each agent, the installed managed `launch_with_hook_watch.py` was invoked
directly with its existing provider and hook configuration and
`AGENT_CONTEXT_HOME` set to a nonexistent child of the private temporary test
directory. This deliberately changes the root for the failure test; it is not
an invocation of the root-setting wrapper. Codex used the same read-only exec
options; Claude used `-p`, `--tools ''`, `--strict-mcp-config`, `--max-turns 1`
and JSON output. Each was asked to report the supplied registry warning without
using tools. Both exited zero, the monitor reported a warning and a completed
hook, and each response quoted that the registry was missing or inaccessible
and to continue with the manual fallback. This verifies the tested missing-root
case, not every possible filesystem or hook failure.

These follow-ups used two of the additional Codex requests and one of the
additional Claude requests. The active VS Code WSL chat interfaces remain
untested. Read-only Windows UI Automation later exposed VS Code control labels,
including Claude Code and Codex tabs, but did not execute either chat test. The
operator agreed to help exercise the interfaces manually.

For the pending VS Code checks, the operator was given this synthetic prompt
for a new chat in each extension, with permission limited to the one read-only
search command. This is a procedure, not a passed result:

```text
Synthetic registry acceptance check. Run this one read-only command in WSL:

AGENT_CONTEXT_HOME=/mnt/c/Users/jimle/ai-dist-mem PYTHONPATH=/home/lehmer/repos/agent-context/src python3 -m agent_context search acsynthetic20261108stio5b

Report the command output and your native session ID and lifecycle event only
if you can actually observe them; identify the source. Otherwise say
unavailable. Do not modify files or guess an ID.
```

Record each extension's actual execution host, result, observed native ID and
event sources, or the specific unavailable capability; do not infer the
extension's hook behavior from a CLI result.

## 2026-11-08 — operator-run VS Code WSL lookups

The operator ran the preceding prompt in new Claude Code and Codex extension
chats in the WSL-connected window and supplied the outputs. Both reported the
same two expected synthetic records. Codex reported command exit zero; Claude
reported that the command changed nothing. Neither agent could itself confirm a
native session ID or a lifecycle event from its available context. Claude
identified `b2394d16-b918-4963-8309-ae1fdc7a04f1` only as a scratchpad-path
candidate, and correctly did not treat it as verified.

A subsequent read-only inspection checked only metadata and the distinctive
synthetic marker in local session records, without copying transcript text.
The Claude session file
`~/.claude/projects/-home-lehmer-repos/b2394d16-b918-4963-8309-ae1fdc7a04f1.jsonl`
contains the test marker in records whose explicit `sessionId` field is
`b2394d16-b918-4963-8309-ae1fdc7a04f1`. This corroborates the native ID beyond
the scratchpad path. The matching new Codex rollout's `session_meta` has ID
`01a1bcc4-3db9-7fd1-9c5f-2279013c8d60`, `source: vscode`,
`originator: codex_vscode` and backend `0.164.0-alpha.11.1`; it contains the
unique marker as a user message and tool call and has `task_started` and
`task_complete` event messages. Those are observed **turn** events, not a
claimed SessionStart or SessionEnd hook. The session records remain in their
native locations; no transcripts were added to the registry or this report.

The extension tests therefore establish lookup and independently observed
native references for these sessions. They do not establish whether either
extension runs the setup's SessionStart hook, whether the hook's native ID
matches the corresponding session, or how that extension behaves when the
registry is unavailable. Keep this step pending until the applicable checks
pass or the specific gap is escalated.

An inert disposable project was prepared at
`/tmp/agent-context-vscode-acceptance-9li94vgp` to make the next check
reviewable. Its `.claude/settings.local.json` and `.codex/config.toml` each
configure a project-scoped SessionStart command pointing to copies of this
checkout's `hook_context.py` and `hook_watch.py`. The command selects the
shared registry root for the hook. A local synthetic invocation of each copied
hook returned valid SessionStart guidance; this is not evidence of extension
hook execution. These hooks have no wrapper monitor and explicitly warn of that
limit. The project has not been opened or trusted in VS Code. Opening and
trusting the folder or hooks may record trust decisions in the operator's VS
Code or agent profile, so that decision is left to the operator under the
execution protocol. No personal configuration was changed to prepare it.

## 2026-11-08 — project-scoped VS Code start hooks

The operator opened the prepared WSL project and ran the synthetic prompt in
both extensions. Claude reported `SessionStart` and UTF-8 base64
`NWI4MTI4MGItYjViMi00Y2ZhLWE2ODAtNDVkZDc4MDFlNjZm`; decoding yields
`5b81280b-b5b2-4cfa-a680-45dd7801e66f`. The matching local Claude session file
for the temporary project contains the distinctive test marker and the same
explicit `sessionId`. Claude also reported the expected warning that the
wrapper monitor was not active. This verifies the observed start-hook context
and reference for this extension session, not all failure modes.

Codex responded `Unavailable`. Its matching native session record has
`source: vscode`, backend version `0.164.0-alpha.11.1`, and both session and
turn working directories equal to the prepared project. The record includes
task-start and task-complete events but does not establish hook execution.

To diagnose the gap without changing the user's settings or making a model
request, the exact VS Code extension backend was launched in a temporary home
with this project marked trusted. Its experimental app-server `config/read`
and `hooks/list` calls reported the project SessionStart definition loaded,
enabled, and **untrusted** in that isolated profile. This establishes the
project configuration is discoverable and that project trust alone does not
trust the hook in that profile; it does not prove the actual VS Code profile's
hook trust state or why its hook was not observed. [OpenAI's hook
documentation](https://learn.chatgpt.com/docs/hooks) describes separate review
and trust for non-managed hooks and the CLI `/hooks` review flow. No trust
bypass was used. The current authorized Codex request allowance is treated as
exhausted; a further real prompt requires a fresh decision.

The operator additionally reported that Copilot answered `Unavailable` to the
synthetic check. The precise Copilot interface, execution host, hook
configuration, and session metadata were not supplied with that result. It
does not establish a passed Copilot integration or a hook event. The dedicated
Copilot/desktop step remains pending behind its declared prerequisites.

The operator subsequently submitted the synthetic missing-root prompt in
Claude Code and reported `READY` with warnings that the registry was missing
or inaccessible and the hook monitor was inactive. A read-only inspection of
the corresponding Claude session file confirmed the unique test prompt,
working directory `/tmp/agent-context-vscode-failure-xz6c_u5q`, native session
ID `977e96d7-2c1f-4ac8-8921-550108d66c55`, and the assistant's missing-root
warning. The turn continued. Together with the independently observed Codex
VS Code warning and continuation, this completes the step's tested
failure-open cases. Forced hook interruption and timeout for these manual VS
Code hooks, and resume in either extension, were not tested and are not
claimed. Earlier statements in this chronological record that the Claude
VS Code check is pending are superseded by this result.

## 2026-11-08 — Windows/WSL real-agent overlap, partial

Following completion of step 02, a disposable Windows profile was staged with
Windows Python 3.14.4, checkout source and the local pure-Python PyYAML
package. The setup script configured the Windows Claude 2.1.317 launcher for
`C:\Users\jimle\ai-dist-mem`; Windows Codex was not found and the VS Code
Copilot shim remains unverified as a standalone CLI. Windows Claude credentials
and minimal account metadata were copied only into the disposable profile and
the profile was removed afterward. The WSL Codex 0.157.0 launcher used an
isolated profile with the matching `/mnt/c/Users/jimle/ai-dist-mem` root; its
temporary credential copy was removed afterward. No personal agent settings
were modified by these profiles.

The first staging attempt failed before a model request because PowerShell
passed a quoted `python -c` probe incorrectly; its disposable profile was
removed. After correcting the probe, one synthetic, tool-free Windows Claude
session and one WSL Codex session ran concurrently. Their observed native IDs
were `a6397bb9-6b48-4dde-984a-bca0116263dd` and
`01a1bd7b-46c2-7863-b736-79a4171b092e`. While both agent processes remained
alive, separate Windows and WSL registry CLI processes concurrently created
records `acr_70f73760d0cf457d800d1506d1374bd3` and
`acr_d3ae932d81c94df09f3fcf63dfc249a5`, respectively. The registry processes
were test-harness processes, not tool calls made by the agents. Both agents
subsequently completed, and Windows Claude's final native ID matched the
requested and initialized ID.

Both host CLIs searched `acsynthetic-crosshost-20261108` and found both
records under their respective spellings of the selected root. Both Windows
and WSL Git read `https://github.com/dullroar/agent-context.git` as the origin;
the records use `git:https://github.com/dullroar/agent-context.git` as their
shared identity and store separate Windows and WSL path hints. These two
test-owned records remain for further cross-host visibility and must be
removed after the acceptance work. This establishes the described overlapping
processes and independent writes, not agent-authored registrations or
network-share semantics. Filesystem stress and VM/RDP checks remain pending.

## 2026-11-08 — shared-volume concurrency and interrupted writes

Outside the sandbox, `python3 /tmp/agent-context-cross-stress.py` created a
unique child of the selected Windows-profile root with a space-containing
subdirectory. Windows Python 3.14.4 loaded the checkout and local PyYAML over
the WSL UNC path; WSL used Python 3.12.3 and the checkout. Eight Windows and
eight WSL registry processes were launched concurrently. All exited zero and,
with the seed, produced 17 unique valid records. The longest resulting Windows
path was 197 characters. Each host's registry CLI validated `17 valid, 0
invalid`.

For each host, a synthetic fixture patched `os.link` inside its own writer
process to signal a barrier immediately after the registry temporary file was
written and flushed but before the final link. That writer was then killed.
The test confirmed that the set of published `.md` files did not change, the
seed record's SHA-256 remained unchanged, and both host validators still
reported all 17 valid. This tests interruption at that specific pre-publish
point; it does not prove behavior at every crash point or on remote storage.
The test removed only its unique child afterward. The script and fixture were
`/tmp/agent-context-cross-stress.py` and
`/tmp/agent-context-interrupt-fixture.py` in this run.

Read-only environment checks reported Windows `SESSIONNAME=Console`, no
`CLIENTNAME`, a running RDP client process, and a configured consumer OneDrive
directory at `C:\Users\jimle\OneDrive`. A client process alone does not
establish an available or authorized remote VM, its drive-redirection policy,
or VM WSL access. OneDrive existence and a running sync process do not prove
cloud or cross-device visibility or conflict handling. Neither the RDP target
nor OneDrive has been used for test data. An appropriate decision and access
are still needed for an approved share/sync comparison; do not treat these
readiness observations as passed remote-storage checks.

For a concrete optional comparison, `/tmp/agent-context-onedrive-test.py` was
prepared but **not run**. If separately authorized, it creates a uniquely named
child under the configured consumer OneDrive path, writes two synthetic
registry pointers from Windows and WSL, checks local visibility from both, and
deletes that child. It cannot by itself prove cloud convergence, another
device's visibility, or cross-device conflict behavior; remote deletion and
recycle-bin retention would also need to be treated separately. Microsoft
documents [OneDrive sync and availability status](https://support.microsoft.com/en-us/onedrive/what-do-the-onedrive-icons-mean)
and notes that [simultaneous changes across PCs can cause sync conflicts](https://support.microsoft.com/en-us/onedrive/restrictions-and-limitations-in-onedrive-and-sharepoint?ad=us&rs=en-001&ui=en-us).
These are documented risks, not observed results for this registry or account.

The operator approved that OneDrive test and reported that VM/RDP testing is
not possible from this environment; the operator plans a separate follow-up
from work. Running `python3 /tmp/agent-context-onedrive-test.py` outside the
sandbox created a unique child under the configured consumer OneDrive root.
One WSL and one Windows registry CLI independently created synthetic records;
both host CLIs found both records through their respective path spellings.
The script removed the test-owned child. Cloud upload, deletion propagation,
recycle-bin retention, another device's visibility, and actual sync-conflict
behavior were not independently verified. VM Windows, VM WSL, RDP drive
redirection and reconnect remain **untested**, not passed.

For a controlled local comparison of registry conflict handling, a disposable
local root was used to create one synthetic record and then copy it twice in
separate scenarios. A canonical `-device.md` duplicate with the same record ID
was listed twice and both files validated; `show` rejected the ambiguous ID
with exit 1. A filename ending ` (conflicted copy).md` was reported as
noncanonical by `validate` with exit 1, while the original record's SHA-256
remained unchanged. This simulates possible file shapes; it does not claim
that OneDrive created those names or that its sync conflict handling was
observed. The comparison indicates manual inspection and reconciliation are
needed rather than assuming a sync client resolves registry records safely.

## 2026-11-08 — trusted Codex VS Code start hook

The operator authorized one additional synthetic Codex request and the
previously described review of this disposable project's hook. The actual
Codex profile contained no trust entry for the project hook. Using the exact
VS Code extension backend `0.164.0-alpha.11.1` in the project directory, the
normal interactive review showed the project SessionStart hook as new and
untrusted. After inspection, it was trusted through that interface; its
recorded trust hash matched the previously inspected hook definition. This
created a project-specific trust entry in the user's Codex profile; it should
be removed or revoked when the disposable project is retired. No trust bypass
was used.

Windows UI Automation was used only on the uniquely identified disposable
VS Code project window to open a new Codex chat and submit the single
authorized prompt `acsynthetic-vscode-trusted-20261108`. It reported
`SessionStart` and base64
`MDFhMWJjZDktYzkxYy03MWQxLWFhOTItNjJjMWQwN2I3MzFh`. The decoded value
`01a1bcd9-c91c-71d1-aa92-62c1d07b731a` matches the `session_meta` ID in the
matching local VS Code session record. The command-free synthetic turn
completed. No transcript text was copied into the registry.

Both extension start events and IDs are now observed, but a missing-root
failure-open check has not been exercised independently in each VS Code
extension. The CLI missing-root checks and Claude's monitor-inactive warning do
not prove those remaining interface-specific cases. Keep the step pending.

For a reviewable next check, an inert disposable project was prepared at
`/tmp/agent-context-vscode-failure-xz6c_u5q`. Its project-scoped Claude and
Codex hooks point to the deliberately nonexistent `missing-registry` child;
the copied hooks match the checkout and the shared registry is not modified.
This project has not been opened or trusted in VS Code. A local synthetic
invocation of each hook returned the missing-root warning in
`hookSpecificOutput.additionalContext`; its `systemMessage` instead carried
the separate warning that the wrapper monitor was inactive. An initial local
assertion expecting the missing-root warning specifically in `systemMessage`
failed; inspection showed why, and the corrected field check passed for both
hooks. This does not establish what either actual VS Code extension displays
or whether an authenticated turn continues. Those tests remain pending and
would require additional authorized model requests and project/hook trust.

## 2026-11-08 — VS Code missing-root tests and Windows readiness

The operator authorized up to ten additional synthetic requests per agent for
the remaining acceptance checks and trust for the disposable failure project.
The WSL-connected VS Code window opened that project. The Codex project's
folder and specific SessionStart definition were reviewed and trusted using
the normal interactive CLI flow; both decisions are test-owned and require
cleanup. Windows UI Automation then selected the Codex extension and sent one
synthetic prompt in a new session. Codex VS Code backend
`0.164.0-alpha.11.1` completed the turn, native session ID
`01a1bce8-6e62-72f3-8738-03e23ec8fb20`, reporting that the registry was
missing or inaccessible and the monitor was inactive. This is a passed
missing-root warning-and-continuation observation for that interface, not a
timeout or forced-interruption test.

A new Claude Code extension session was opened in the same project. UI
Automation's value-setting placed the synthetic prompt in its composer, but
the `Send message` control remained disabled; keyboard injection attempts did
not register a diagnostic keystroke. No Claude prompt was submitted by this
automation. The operator was asked to retype and submit the exact prompt and
return the result. Until that happens, the Claude VS Code missing-root check
remains untested and this step remains pending.

The operator later supplied the expected `READY` and missing-registry warning.
Read-only inspection showed the distinctive Claude-test prompt in the already
observed Codex VS Code session `01a1bce8-6e62-72f3-8738-03e23ec8fb20`; the
Claude composer in the test window still contained the prompt unsent, and no
matching Claude session record was found. Consequently that response is a
second Codex observation, not evidence of the Claude interface. The operator
was asked to submit the prompt in the Claude Code pane or report if its Send
control remains disabled. No transcript text was added to this record.

Read-only Windows readiness probes found native Claude Code 2.1.317 signed in
using `claude.ai`, Windows Python 3.14 and Git, and the selected profile's
`ai-dist-mem` directory present. No Windows Codex command was found; Windows
`copilot` resolved to a VS Code shim whose standalone operation remains
unverified. These are readiness observations only: no downstream Windows-agent
or cross-host acceptance step has been started while its prerequisite is
pending.
## 2026-11-08 — Copilot CLI and desktop readiness, partial

The WSL Copilot CLI 1.0.107 was exercised in a disposable profile with the
selected shared registry. An initial invocation failed before a request because
`--session-id` and `--trust-folder` are incompatible. A second failed before a
request because the existing GitHub CLI token is a classic PAT, which Copilot
rejected. The sandboxed `gh auth status` had earlier failed, while the same
read-only status check outside the network-restricted sandbox succeeded; this
is a context distinction, not proof the token was invalid.

The successful attempt copied only account-selection metadata into a fresh
disposable Copilot profile and used the already configured keyring. It used the
managed launcher, a one-session folder-trust flag, no builtin MCPs, no tools
requested, and one synthetic prompt. `sessionStart` guidance reached the model;
the reported base64 `NjNlYWUwNDItMmE4Yi00NmZhLThjZTgtNmM4MGU5NjVkODY0`
decodes to `63eae042-2a8b-46fa-8ce8-6c80e965d864`, matching the CLI result's
native session ID. Exit was zero, the monitor reported completion, and the
result reported **one premium request**. The disposable Copilot profile was
removed. A test harness registered pointer
`acr_d801af25851b4f5587084151ac8f1473` on the shared root; both WSL and
Windows registry CLIs found it. It is retained temporarily with the other
test-owned pointers for later cleanup.

A bounded Windows VS Code Copilot shim `--version` probe in a disposable
profile returned exit 127 and reported that the standalone GitHub Copilot CLI
was not found; no installation was attempted. A Windows Codex/ChatGPT desktop
package has running processes and one top-level window; the Claude Desktop
process was not running. Presence does not establish a separate usable
desktop session, its host, hooks, or registry access. The VS Code local-agent
and actual desktop checks are not yet complete.

Although `codex` was absent from the Windows PATH, the running desktop package
provided a native backend executable. Its `--version` and `--help` probes in a
disposable profile passed; the reported version was `0.167.0-alpha.3.2`. With
that executable's directory temporarily added to the test process PATH, the
Windows setup script installed a disposable Codex launcher for the selected
shared root and correctly reported its hook integration unverified. One
authenticated, read-only, tool-free synthetic turn completed with native
thread ID `01a1bd93-7fd1-7ca1-a28c-e643d0bfe10a` and response `READY`.
A Windows registry process then created test-owned pointer
`acr_20129920fd5946d8b379bb34f1ecb103`, which Windows and WSL each found. The
disposable profile and credential copy were removed. This tests the bundled
backend as a Windows CLI, not the desktop GUI or a Windows hook.

A second isolated authenticated WSL Copilot CLI turn invoked the managed hook
monitor directly with `AGENT_CONTEXT_HOME` set to a deliberately nonexistent
temporary path. It completed with exit zero, the monitor reported a hook
warning and completion, and the response quoted the missing-or-inaccessible
registry warning and manual fallback. This test exercised the direct monitored
launcher, not the root-setting wrapper. It reported one additional premium
request; the isolated profile was removed. Resume, every hook failure mode, and
actual VS Code behavior are not inferred from this check.

A project-scoped Copilot `sessionStart` hook was prepared in the disposable WSL
VS Code project `.github/hooks/agent-context.json`; a local synthetic payload
produced valid Copilot `additionalContext`, not evidence of a VS Code run. A
new standard VS Code Chat was selected in **Agent / Local** mode; its visible
model picker reported `qwen3.8:latest`. UI Automation did not successfully
populate the Monaco composer or enable Send, so the operator was asked to submit
the synthetic prompt and report the model and result. No automated VS Code
Copilot prompt was submitted.

Read-only Windows UI Automation found the running desktop Codex application's
top-level window, but exposed only its window-frame controls, not the chat
composer or a way to select an isolated session. No desktop conversation was
opened or model request sent by the inspection; desktop host, hooks and
registry access remain untested.

For a Windows-native desktop check, an empty disposable project directory was
prepared at
`C:\Users\jimle\AppData\Local\Temp\agent-context-desktop-acceptance-c91096d9a34d4c5380c313c58b1dbe42`.
It contains no Linux-only project hooks. The operator was given a revised
Windows PowerShell search procedure using the profile registry and the WSL UNC
source/dependency paths. The session and its result are still pending; remove
the empty test directory after it is no longer needed.

The operator subsequently completed the synthetic VS Code Local-target turn
and reported `READY` with the startup event and native ID unavailable. A
read-only inspection of the matching synthetic session metadata found
`session.start` with native session ID
`11056049-2b95-495f-8a77-0db6a0914388` in the WSL extension-host session
storage; the model had not been given a usable hook event or ID. No transcript
content was copied into the registry. The user reported the machine was busy
and the turn took a while; the selected model previously displayed
`qwen3.8:latest` and its local model service was listening, but the prompt's
actual resource use was not measured.

The test instruction mistakenly specified VS Code's **Local** session target.
The [VS Code hook documentation](https://code.visualstudio.com/docs/agent-customization/hooks)
distinguishes that older Local harness from the separate **Copilot** target and
its event and output contracts. UI inspection confirmed an enabled Copilot
target is offered in this test window. Accordingly, the Local result does not
verify the prepared Copilot hook or the VS Code Copilot target, which remains
untested. The correction does not require installing extensions or changing
the existing Copilot CLI setup.

## 2026-11-10 — resume check; step 04 blocked on operator interaction

Resumed from the 2026-11-08 checkpoint. `PYTHONPATH=src python3 -m unittest
discover -s tests` ran 75 tests, OK with 15 skipped; `bash -n scripts/setup.sh`
and `git diff --check` passed. The six retained synthetic pointers are still
present on `/mnt/c/Users/jimle/ai-dist-mem` (one file each for the IDs listed in
the handoff checkpoint). The Windows desktop test directory still exists. The
two disposable WSL projects under `/tmp/agent-context-vscode-*` no longer exist,
so the prepared VS Code Copilot hook project (`.github/hooks/agent-context.json`)
would have to be recreated; their Codex trust entries may still persist in the
user's Codex profile and are not yet cleaned up.

No new interface check was run. Still **untested**: the VS Code Copilot-target
session (the earlier Local-target result does not count), the desktop GUI
session, VM/RDP, and cross-device OneDrive sync/conflict behavior. The remaining
checks need the operator to submit prompts in a GUI (UI Automation could not
populate the Copilot composer or the desktop Codex chat) and a fresh decision on
further synthetic requests. Steps 04 and 05 remain `pending`.

## 2026-11-10 — VS Code WSL Copilot target, pointer created

The operator opened the recreated project
`/tmp/agent-context-vscode-copilot-acceptance` in VS Code and reported that its
Copilot target ran the project-scoped `sessionStart` hook. The hook context
reported event `sessionStart`, agent `copilot`, runtime `WSL`, and the session
ID encoded as `OTU3ZjgxY2YtMmI5NS00Y2RjLWIyMjMtMjliNzVjZTVlYmU1`.
Decoded, that value is
`957f81cf-2b95-4cdc-b223-29b75ce5ebe5`. The first turn did not create a record
because `AGENT_CONTEXT_HOME` was unset in the Copilot shell; this was a useful
failure-open result, not a registration pass.

In a subsequent Copilot session, the operator reported another observed
`sessionStart` context and resolved the intended root dynamically from the
Windows profile to `/mnt/c/Users/jimle/ai-dist-mem`. That session used its
own observed ID `4fa1b87e-14a8-4068-88cb-61b91953c244` and registered synthetic
record `acr_0ac5b461afa74809ac89cf90a2d16c45` with vendor/producer `copilot`,
project identity `test:agent-context-vscode-copilot`, title `VS Code Copilot
acceptance test`, and status `unknown`. The operator's `show` and title-search
commands succeeded. Independent WSL CLI checks on 2026-11-10 also succeeded:
`AGENT_CONTEXT_HOME=/mnt/c/Users/jimle/ai-dist-mem
PYTHONPATH=/home/lehmer/repos/agent-context/src python3 -m agent_context show
acr_0ac5b461afa74809ac89cf90a2d16c45` displayed the exact session ID and
metadata, and the same environment with `search 'VS Code Copilot acceptance
test'` returned that record.

The separate-session Copilot lookup had not yet been observed at this checkpoint.
The record then proved pointer creation and CLI lookup, not cross-session
discovery or resume.

## 2026-11-10 — final reconciliation and cleanup

The operator completed a separate VS Code WSL Copilot session. Its hook supplied
event `sessionStart`, agent `copilot`, runtime `WSL`, and native session ID
`65df54ce-cc88-448b-a43d-d078fcb18aaf`, which differs from the native ID on
pointer `acr_0ac5b461afa74809ac89cf90a2d16c45`. In that separate session, the
operator reported successful `show` and title-search commands against
`/mnt/c/Users/jimle/ai-dist-mem`. The lookup did not create or update a record.
Together with the independent WSL CLI checks recorded above, this verifies the
VS Code Copilot target, observed session identity, shared-root pointer, and
cross-session lookup. Resume was not tested.

### Acceptance matrix

| Requirement | Result | Evidence and limits |
| --- | --- | --- |
| R1 — WSL CLI | Pass | Mounted Windows-profile root baseline passed register/list/search/show/validate, spaces and UTF-8, multiple topics, concurrent creates, and simulated write failure. Exact commands and WSL environment are in the 2026-11-08 baseline section. |
| R2 — Real interfaces | Pass for available required targets | WSL Claude and Codex CLI, separate VS Code Claude/Codex targets, observed native IDs, and cross-session lookups are recorded above. Resume and forced hook interruption/timeout remain untested. |
| R3 — Windows/WSL and VM | Pass for available Windows/WSL checks; VM and cloud sync untested | Windows Claude and Codex plus WSL Codex overlapped on the selected root; both host CLIs found each other's records. Concurrent and interrupted writes passed. Local OneDrive visibility was observed, but cloud convergence and cross-device conflict behavior were not tested. VM/RDP was unavailable. |
| R4 — Copilot/desktop | Pass for WSL Copilot CLI and VS Code WSL Copilot; other interfaces untested | Copilot CLI failure-open and registration checks passed. The VS Code WSL Copilot hook and separate-session pointer lookup passed. The Windows VS Code Copilot shim was unavailable, and UI Automation could not use the running desktop Codex chat composer; no desktop GUI conversation was run. |
| R5 — Honest result | Pass | This matrix distinguishes tested checks from unavailable or untested interfaces. No resume, VM/RDP, cloud convergence, cross-device conflict, or desktop GUI success is claimed. |

Final validation on 2026-11-10 from the repository root:

- `PYTHONPATH=src python3 -m unittest discover -s tests` — 75 tests ran,
  passed; 15 skipped.
- `bash -n scripts/setup.sh` — passed.
- `git diff --check` — passed.
- Independent WSL CLI `show` and `search` found the Copilot pointer before
  cleanup. The operator's separate Copilot session also reported both lookups
  succeeded.

Cleanup verified each of the six retained synthetic records listed in the
handoff checkpoint and the new Copilot acceptance pointer by exact registry
ID and synthetic marker before removing only those seven files. A registry
scan reported zero read errors. The disposable project
`/tmp/agent-context-vscode-copilot-acceptance` was removed. No unrelated
registry entries or personal settings were changed; any VS Code workspace-trust
entry was not inspected or modified.

Steps 04 and 05 are done for the checks available under this plan. The
untested items above remain limits on the evidence, not acceptance passes.
