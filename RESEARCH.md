# Interoperability research

Initial inventory: 2026-11-06; research update: 2026-11-07. This is a design
inventory, not a claim that any project below has adopted this repository's proposed record format.

## Conclusion

No single mature open standard was found that jointly covers local
cross-vendor coding-agent session discovery, portable long-term memory,
tamper-evident provenance, and lifecycle management. The ecosystem has useful
parts; this project should compose with them rather than recreate them.

| Concern | Closest existing work | Fit | Deliberate gap for this project |
| --- | --- | --- | --- |
| Tool/data connectivity | [MCP](https://modelcontextprotocol.io/specification/) | Strong for exposing tools, prompts, and resources | It does not prescribe shared memory semantics or a portable local session registry. |
| Agent-to-agent collaboration and task lifecycle | [A2A](https://a2a-protocol.org/v1.0.1/topics/life-of-a-task/) | Strong for remote task state, artifacts, and `contextId` | It does not provide a human-facing catalog of local vendor sessions. |
| Portable agent memory | [Open Memory Protocol Initiative](https://ai-disclosures.org/ompi) and the [W3C memory interoperability CG](https://www.w3.org/community/ai-agent-memory-interop/) | Directly aligned with vendor-neutral memory portability | Still emerging; memory portability is broader than session discovery. |
| Observability correlation | [OpenTelemetry GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai) | Useful names for agent, conversation, message, and trace correlations | Telemetry does not supply persistent human discovery records. |
| Tamper-evident provenance | [in-toto Attestation Framework](https://in-toto.io/docs/specs/) and [SLSA provenance](https://slsa.dev/spec/v1.2/build-provenance) | Mature models for signed software-supply-chain statements | Their build-artifact focus is not a reason to impose signatures on local session notes. |

## Design implications

1. **Adopt concepts, not a false umbrella.** Use opaque native IDs; make room
   for OpenTelemetry correlation IDs; map lifecycle states to A2A only when an
   adapter actually speaks A2A.
2. **Do not compete with portable-memory initiatives.** A later adapter may
   link a session record to an OMP/W3C-compatible memory object, but v0 stores
   neither a memory graph nor a transcript.
3. **Use Git before cryptography.** For a versioned registry, Git commits offer
   inexpensive provenance. Add in-toto/SLSA-style attestations only for a real
   verification boundary.
4. **Keep MCP optional.** An MCP server could expose `register`, `search`, and
   `inspect` after the file format and CLI have proved useful. It should remain
   an adapter, not a prerequisite.

## Initial findings: Copilot and a shared drive

Checked 2026-11-07 against the documentation below; these are documented
capabilities, not local test results. [The research plan](plans/research/spec.md)
starts by expanding these into a version- and environment-specific matrix.

- **Copilot and VS Code:** [VS Code's hook guide](https://code.visualstudio.com/docs/agent-customization/hooks)
  describes separate Copilot, Claude and Codex session-target implementations,
  and lists Copilot session, prompt, tool, compaction and subagent events. It
  says its hooks experience is preview and enterprise policy may restrict hooks
  and provider harnesses. The [GitHub hooks overview](https://docs.github.com/en/copilot/concepts/customizations/hooks)
  distinguishes executable hooks from instructions to a model. Subsequent
  local CLI findings are recorded below; VS Code and desktop event coverage
  remains untested.
- **RDP client drive:** Microsoft documents access to the RDP client's local
  drives from the remote session when drive redirection is enabled and permitted,
  and uses `\\tsclient\c\myfiles` in an [example](https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/copying-2-gb-file-by-clipboard-redirection-fails).
  Thus a VM Windows process may be able to use
  `\\tsclient\C\Users\<username>\ai-dist-mem` while connected. This is a
  proposed deployment path, not a known available location; an organization's
  [policy can disable drive redirection](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-remotedesktopservices#donotallowdriveredirection).
  Treat disconnect/reconnect, concurrent access, permissions and any data
  transfer restrictions as test and policy questions.
- **WSL:** Microsoft documents [DrvFs mounting of network paths](https://learn.microsoft.com/en-us/windows/wsl/release-notes)
  generally. Whether this particular redirected RDP path is reachable from a
  particular VM's WSL instance, under its user context and policy, is unknown;
  verify it independently rather than assuming that a Windows path translates.
  Atomic replacement, interruption recovery and synchronization behavior for
  this filesystem combination are also untested.

## Copilot: interfaces and lifecycle (investigated 2026-11-07)

**Evidence and versions.** Official documentation was read on 2026-11-07;
its online pages are rolling documentation, not a pinned installed version.
This host reports WSL2 Ubuntu 24.04, VS Code remote CLI 1.145.2, Claude Code
2.1.319, Codex CLI 0.157.0 and, after installation, GitHub Copilot CLI 1.0.107
via `uname -a`, `$WSL_DISTRO_NAME`, and `--version`. The Linux Copilot binary
now precedes the Windows VS Code shim on `PATH`; the earlier shim-only finding
has been superseded. `code --list-extensions --show-versions` did not provide a
usable list in this shell. The CLI observations below do not establish support
for VS Code, desktop, Windows-native, VM, cloud or enterprise-policy scenarios.

| Surface / host | Documented mechanism and execution | Result here |
| --- | --- | --- |
| VS Code Local | Local harness works through the workspace extension host; its legacy hook payload and settings are distinct from the Copilot runtime. | WSL remote CLI found; UI/hook behavior untested. |
| VS Code Copilot target | Shared Copilot harness runs on local machine, connected WSL/SSH host, or dev container; verify actual runtime host and environment for each session. | Selection, hook discovery, WSL execution and access to registry untested. |
| VS Code Claude/Codex target | Uses provider harness and its hook rules; selecting a Claude/OpenAI *model* under Copilot does not switch harness. | Target availability and hooks untested; enterprise policy can disable targets. |
| Copilot CLI | Same documented Copilot runtime/hook format; supports user and repo hooks, with shell-specific `bash`/`powershell` entries. | WSL CLI 1.0.107 installed; instruction and skill discovery and a no-prompt `sessionEnd` hook observed locally, as detailed below. Other lifecycle and authenticated model behavior untested by this investigation. |
| GitHub Copilot app | VS Code describes the app as sharing the Copilot harness and hook format; app runtime and paths remain environment-specific. | Availability, OS, versions and hooks unknown. |
| Remote/Cloud/Copilot coding agent | Remote session runs on connected host; cloud uses a managed environment, with separate filesystem/configuration and provider/event limitations. Local hook files are not automatically copied. Cloud feature/status and permissions vary. | No remote or cloud agent session tested; no access to local roots assumed. |

Sources: [VS Code harnesses](https://code.visualstudio.com/docs/agents/concepts/agent-harnesses),
[VS Code hooks and remote execution](https://code.visualstudio.com/docs/agent-customization/hooks),
[Copilot CLI hooks](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-hooks),
and [Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference).
VS Code calls its hooks experience preview; features and policy can vary by
version and organization. The documented enterprise-managed settings may disable
Claude/Codex harnesses; check actual organizational policy, not just UI controls.

**Documented event contract.** Copilot `sessionStart` covers start and resume;
its input includes `sessionId`, `cwd`, `source` (`startup`, `resume`, or `new`),
and potentially `initialPrompt`. `sessionEnd` has a reason; `agentStop` is an
end-of-turn event, not proof the session ended. `userPromptSubmitted`,
`preToolUse`, `postToolUse`/`postToolUseFailure`, `preCompact`,
`subagentStart`/`subagentStop` and `errorOccurred` have distinct meanings and
coverage. CamelCase and PascalCase names choose different input field formats;
not every event/output applies to every runtime, and the reference notes that
some built-in subagents do not emit subagent events. Do not log whole input:
fields can include prompt text, tool arguments/results or transcript paths.
The ID is an opaque native pointer; neither portability nor resume is proven by
its presence. [Reference: input fields and event coverage](https://docs.github.com/en/copilot/reference/hooks-reference).

**Configuration and error handling.** Documented repository hooks live in
`.github/hooks/*.json`; personal CLI hooks can live under `~/.copilot/hooks/`
or `$COPILOT_HOME/hooks/`. Sources can accumulate; check for duplicate hooks,
permissions and the `cwd`/dependencies of the actual host. On the documented
Copilot runtime, a `preToolUse` command crash or nonzero exit denies the tool,
while its timeout falls through to normal permission handling; other events
have different failure rules. Registry hooks must not introduce denial on a
storage error: prefer a suitable non-blocking event and test the actual host's
behavior. [GitHub reference: locations, cloud and exit codes](https://docs.github.com/en/copilot/reference/hooks-reference).

**Instructions and skills.** GitHub documents `SKILL.md`-based skills across
Copilot app/CLI/cloud and VS Code agent mode, with loading based on relevance;
repository instructions are a separate mechanism. Copilot CLI documents
`.github/copilot-instructions.md`, `AGENTS.md` and `CLAUDE.md` discovery,
plus `/instructions` to inspect the active files; the exact rules vary by
client and version. See [Copilot CLI instruction locations](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions).
A skill is not an enforced hook or evidence that it loaded. Use a short always-applicable instruction and
an optional skill for detailed procedure, subject to host-specific support and
policy. [GitHub customization comparison](https://docs.github.com/en/copilot/concepts/customizations/comparing-customizations).

### Local Copilot observations (2026-11-07)

- **Executable and keyring:** `type -a copilot` and `copilot --version` show
  the WSL-installed CLI 1.0.107 before the Windows shim. `dpkg-query` shows
  GNOME Keyring 46.1, libsecret 0.21.4 and Seahorse 43 installed. From the
  regular WSL user session, an outside-sandbox `busctl --user list` check found
  `org.freedesktop.secrets` owned; the sandbox could not connect to the bus
  (`Operation not permitted`). Jim reports that Copilot works after configuring
  the keyring. The investigation did not inspect a token, list keyring entries,
  or independently prove which credential store Copilot used.
- **Instruction discovery:** `copilot --no-auto-update instruction list
  --json` in this repository returned its `AGENTS.md`. In a disposable Git
  repository under `/tmp`, the same command with an isolated `COPILOT_HOME`
  returned synthetic `AGENTS.md` and `CLAUDE.md` files. These are discovery
  results; no model response was used to prove instruction following.
- **Skill discovery:** `copilot --no-auto-update skill list --json`, in that
  disposable repository, listed a synthetic `.agents/skills/` skill as enabled
  and project-sourced. This confirms discovery, not automatic invocation or
  compliance with the skill's instructions.
- **Real no-prompt hook:** A disposable repository hook configuration contained
  `sessionStart` and `sessionEnd` command hooks. A Python probe recorded only
  the event label, whether a session ID was present, whether `cwd` matched the
  project, and event source/reason; it did not persist IDs, prompts, transcripts
  or credentials. Two interactive sessions were started with
  `COPILOT_HOME` pointing to a disposable directory, `--no-auto-update` and
  `--sync-session=off`; folder trust was granted for the session only and each
  was closed with `/exit`, with no model prompt. Both invoked `sessionEnd` with
  `sessionId` present, matching `cwd`, and reason `user_exit`. Neither invoked
  `sessionStart` in this no-prompt scenario. This does not establish behavior
  after submitting a prompt, on resume, or after a crash.
- **Authentication and cost limits:** The isolated home asked for `/login`,
  both in the sandbox and outside it; that result does not contradict Jim's
  working normal configuration and does not identify why the isolated one was
  unauthenticated. No model request was made. `copilot help billing` and
  `copilot help limits` say model use can consume AI credits or premium
  requests and describe the session credit cap as soft. Authenticated prompt,
  start/resume, prompt/tool/stop events, hook failure behavior and actual
  cross-session resume remain untested, as do other interfaces and hosts.

The scratch probe lives under `/tmp/agent-context-copilot-research/`; it is not
a production adapter or a replacement for the [WSL acceptance plan](plans/wsl-test/spec.md).

## Claude and Codex: hooks and surfaces (investigated 2026-11-07)

All entries below describe documentation read on that date. Local executable
versions are listed in the Copilot section. Neither version was exercised with
a hook or real session. The installed versions may predate features in rolling
docs. Record actual version, event, host, root, exit/timeout and resume evidence
in the WSL test plan before calling any combination supported.

| Vendor / interface | Documented behavior | Local verification |
| --- | --- | --- |
| Claude Code CLI in WSL | `SessionStart` (including resume), `UserPromptSubmit`, `PreToolUse`, `PostToolUse`/`PostToolUseFailure`, `Stop` and `SessionEnd` hooks; input includes native `session_id`, `cwd`, event and often transcript path. | Claude 2.1.319 found; no hook/session run. |
| Claude Code VS Code extension / WSL | Claude's VS Code integration supports remote windows; settings and execution dependencies must be present in the remote environment. The settings guide covers local terminal, VS Code and desktop. | UI, extension, event firing and remote paths untested. |
| Claude Code in Claude Desktop | Local Code sessions read Claude Code settings; desktop can also use remote environments, with distinct hosts/configuration and administrator restrictions. General desktop chat is not automatically a Claude Code session. | Desktop presence, session mode, hook events and execution host unknown. |
| Codex CLI in WSL | OpenAI documents `SessionStart` with `startup`, `resume`, `clear`, `compact` and `fork` sources; prompt, pre/post tool, `Stop`, `Interrupt`, `SessionEnd` and subagent events. Common input includes opaque `session_id`, `cwd` and possibly `transcript_path`. | Codex CLI 0.157.0 found; no hook/session test. |
| Codex VS Code / WSL | OpenAI documents the IDE extension and shared CLI/IDE configuration for integrations. VS Code's provider target uses the Codex harness; the remote host and feature availability must be checked for the selected surface. | Extension version, target, hook support and execution host untested. |
| Codex desktop / local or remote | OpenAI documents local Codex hooks and desktop plugin-bundled hooks; scripts must be present in the execution environment and non-managed hooks need trust. Cloud orchestration has separate restrictions and does not load local command hooks. | Desktop version, runtime, configuration, policy and actual hook execution untested. |

Sources: [Claude hook reference](https://code.claude.com/docs/en/hooks),
[Claude settings](https://code.claude.com/docs/en/settings),
[Claude VS Code](https://code.claude.com/docs/en/vs-code),
[Claude Desktop](https://code.claude.com/docs/en/desktop),
[OpenAI hooks](https://learn.chatgpt.com/docs/hooks),
[OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins),
and [VS Code harnesses](https://code.visualstudio.com/docs/agents/concepts/agent-harnesses).

**Event semantics.** A start-on-resume event does not prove the referenced
session can be reopened from another machine. A `Stop` denotes the assistant
stopping its response; it is not equivalent to a process or session exit.
`SessionEnd` is best-effort and can be absent on crash or forced termination.
OpenAI documents `SessionEnd` as advisory and notes that switching away from a
conversation does not immediately end it; its reason is currently `other`.
For both providers, treat state as last observed, never infer completion from
a turn stop, and do not write raw prompt/tool input or transcript content.

**Configuration and failure behavior.** Claude Code documents user
`~/.claude/settings.json` and project `.claude/settings.json`, among other
layers; its `CLAUDE.md` and skills are instructions, not deterministic hook
execution. Exit code 2 blocks a `PreToolUse` or prompt event and can force a
`Stop` to continue, while start/end handling differs. `onFailure`, Windows
shell availability and the exact event also matter. Claude documents 600 seconds
as the default for most command, HTTP and MCP hooks, 30 seconds for prompt
submission, and 1.5 seconds by default for session-end hooks. Timeouts usually
continue the action, with documented policy and Windows shell exceptions.
Never rely on generic exit rules; use a bounded, non-blocking wrapper and test
failure and timeout.
See [Claude hooks](https://code.claude.com/docs/en/hooks) and
[Claude skills](https://code.claude.com/docs/en/skills).

Codex documents hooks in `hooks.json`, inline `[hooks]` in `config.toml`, or
installed plugins; non-managed hook definitions require trust and policy can
limit them. It documents 600 seconds as the default for most hook commands,
but `SessionEnd`/`Interrupt` default to one second and cap at three. Background
hooks can finish out of order and be cancelled at session end; `SessionEnd`
itself is synchronous. For `PreToolUse`, exit 2 can deny a tool, while
unsupported response fields are reported as errors and the tool call continues.
Registry integration should return no denial on failure and must verify the
specific event behavior. A hook must never be assumed to run, finish, or have a
writable root. `AGENTS.md` and `SKILL.md` give guidance; verify discovery for
both CLI and each UI separately. See [OpenAI hook behavior and limitations](https://learn.chatgpt.com/docs/hooks)
and [AGENTS.md guidance](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex).

## Shared-root topology assessment (investigated 2026-11-07)

The following is a deployment comparison, not a filesystem guarantee. No RDP,
VM, SMB, sync client, Windows-native process, or Windows/WSL concurrent write
was tested. A registry root may be shared without sharing vendor session data:
other hosts still need authorized access to the native session to open it.
`project.identity` must be the same neutral value across hosts; each host sets
`AGENT_CONTEXT_HOME` to its own path, with local paths as hints only. A Git
remote may itself contain sensitive information; avoid credential-bearing URLs.

| Topology and example root | Availability and permissions | Concurrent writes, interruption and recovery |
| --- | --- | --- |
| Local WSL filesystem, e.g. `/home/user/ai-dist-mem` | Independent of Windows path; accessible to WSL processes under their permissions. Windows access mechanism and ACLs need verification. | Independent unique files reduce collisions; same-file update races and power-loss durability still need tests. Retain valid old records; repair or discard orphaned temporary files after inspection. |
| Windows local drive, e.g. `C:\Users\<username>\ai-dist-mem`, accessed by Windows and perhaps WSL at `/mnt/c/Users/<username>/ai-dist-mem` | WSL fixed-drive automount is configurable; path and user permissions must be checked independently. Windows ACLs still apply. | Same record may be seen from multiple processes. Test rename/replace, concurrent independent creation, same-file conflicts and interrupted writes on the actual volume. A Linux-looking mount is not proof of Linux filesystem semantics. |
| RDP redirection: desktop `C:\Users\<username>\ai-dist-mem`, VM `\\tsclient\C\Users\<username>\ai-dist-mem` | Available only when the client redirects that drive, the connection and server policy permit access, and the process has rights. This shares data across the remote-session boundary. VM WSL path/reachability is unknown; no automatic `/mnt/c` equivalence. | Disconnect, reconnect, failed/partial writes and cross-host visibility require testing. Do not claim atomic rename, durable flush, reliable locking or offline operation. If unavailable, warn and preserve any previous valid record; do not silently switch roots or reconcile by overwriting. |
| Approved SMB/network share, e.g. `\\server\share\ai-dist-mem`, WSL mount point chosen by administrator | All hosts need authorized connectivity and permissions; WSL mount setup is separate and enterprise-managed. No assumption that UNC and Linux path are interchangeable. | Server/client behavior, network partitions and replace semantics vary. Test unique creates, same-record update races, reconnect, conflicts and crash recovery with disposable data on the actual share. |
| Approved sync folder on each host | A local path may be usable offline but other machines can see stale or missing updates until sync catches up. Enterprise identity, retention, sharing and data policy apply. | This is replication, not a transaction or lock. Concurrent updates can yield conflict copies or last-writer outcomes depending on client/version. Detect and preserve both versions for human reconciliation; never silently delete either. |

[Microsoft WSL configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
describes configurable DrvFs automount and optional mounts; its
[permissions guide](https://learn.microsoft.com/en-us/windows/wsl/file-permissions)
describes the interaction with Windows permissions.
[Microsoft's RDP example](https://learn.microsoft.com/en-us/troubleshoot/windows-server/remote/copying-2-gb-file-by-clipboard-redirection-fails)
uses `\\tsclient\c\...`; [RDP policy](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-remotedesktopservices#donotallowdriveredirection)
can prohibit redirection. [Azure Virtual Desktop documentation](https://learn.microsoft.com/en-us/azure/virtual-desktop/redirection-configure-drives-storage)
says a network drive reconnected during a session may require reconnecting the
remote session before redirection; this is product-specific, not proof of all
RDP clients' behavior. Microsoft describes [non-Office sync conflict copies](https://learn.microsoft.com/en-us/troubleshoot/sharepoint/sync/troubleshoot-sync-issues)
for a OneDrive work/school client; other clients or versions may behave
differently.

**Recommended trial, not a deployment decision:** start with an explicitly
selected local WSL root; then, if permitted and available, test a disposable
Windows directory from local Windows and WSL. Separately try RDP redirection
from the VM's Windows process and then VM WSL, recording whether each can read,
write and see independent files. Exercise reconnect, permissions, spaces,
rename/replace and interruption. Compare an authorized share/sync alternative.
A failed or blocked check is recorded as such; no workplace data, policy
changes or global mount configuration is authorized merely by this research.

## Implementations and protocol crosswalk (investigated 2026-11-07)

These are primary-source README/design claims, not installations, code audits,
security reviews or independently verified compatibility. GitHub metadata on
2026-11-07 showed all three repositories public and not archived; the linked
main-branch commits establish a snapshot, not a guarantee of maintenance.

| Project | License and observed maintenance | Relevant design and limits for v0 |
| --- | --- | --- |
| [agents-memory](https://github.com/Lolaplex/agents-memory) | MIT; [main commit 7973f746](https://github.com/Lolaplex/agents-memory/commit/7973f746e768e2e931839054391899467410f709) dated 2026-11-05 UTC. Its README advertises a Python package and tests; operational maturity not independently assessed. | Particularly relevant: its [catalog](https://github.com/Lolaplex/agents-memory/blob/main/abi/INGEST.md) discovers vendor chat references with title/path and a `chats-index.md`, including Copilot and Claude sources; its README says live Codex rollouts are not yet ingested. Its broader extract/distill pipeline stores derived memory and can use MCP and a disposable FTS index. This project can study catalog discoverability without requiring transcript extraction, a generated index or MCP. Do not claim the discovery need is wholly unaddressed. |
| [agent-memory-vault](https://github.com/mcncarl/agent-memory-vault) | MIT; [main commit 194559d9](https://github.com/mcncarl/agent-memory-vault/commit/194559d9ba19efe43974138601a8edfb1669eba2) dated 2026-10-04 UTC. That commit describes Linux/macOS test coverage and Windows adapter parsing, not full Windows writer parity. | Shared Markdown plus Git, SQLite/FTS, optional vector search, claims and audit; its read-only installation plan, explicit apply and hook backups are useful setup patterns. Its governed vault and state database are broader than this CLI's no-required-database boundary. |
| [projectmem](https://github.com/riponcm/projectmem) | MIT; [main commit a405361b](https://github.com/riponcm/projectmem/commit/a405361b8d12cb773bb42ef0f64004623dbee764) dated 2026-11-01 UTC. README advertises v0.3.5 and tests; not independently run. | Event-sourced project memory, deterministic summaries, prechecks and optional MCP. Its separation of intent, event history and derived projections is useful; its event log and governance purpose are not a replacement for a portable vendor session pointer. |

**Crosswalk and caveats:**

- [MCP specification 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
  defines host/client/server connectivity, tools and resources. A later optional
  registry adapter could expose existing records; MCP is not a v0 storage or
  identity requirement.
- [A2A 1.0.1 task lifecycle](https://a2a-protocol.org/v1.0.1/topics/life-of-a-task/)
  uses `contextId` to group messages and tasks; a task has its own `taskId`.
  Store `a2a_context_id` only when it is actually supplied by an A2A system;
  do not equate it to every vendor's native session ID or map local status
  mechanically to A2A task state. A2A also discusses artifact mutation; it is
  not a local cross-vendor session catalog.
- OpenTelemetry's [GenAI inference conventions](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md)
  define `gen_ai.conversation.id` for correlation. `native.session` could be
  associated with it only when instrumentation says they identify the same
  conversation; `otel_trace_id` is a trace identifier, not a conversation ID.
  Capture either only when actually present, with no telemetry dependency.
- The IBM/Mozilla co-convened [Open Memory Protocol Initiative](https://ai-disclosures.org/ompi)
  describes itself as pre-1.0 and says no reference implementation exists yet.
  The [W3C community group](https://www.w3.org/community/ai-agent-memory-interop/)
  describes its own interoperability profiles and scope; a community group is
  not itself a W3C Recommendation. Neither supplies a verified mapping from
  this session pointer to a portable memory object. Keep any future link
  optional and define it only against a published, tested format.
- [in-toto's attestation framework](https://in-toto.io/docs/specs/) and
  [SLSA build provenance 1.2](https://slsa.dev/spec/v1.2/build-provenance)
  define supply-chain claim/provenance mechanisms. Git history can provide
  ordinary change history but does not itself authenticate an author or make
  tamper-evident attestations. Do not imply equivalent guarantees.

**Recommendation:** continue the small offline pointer registry, explicitly
acknowledging the overlap with agents-memory's catalog. Reconsider an upstream
issue or integration after proving a concrete gap and a safe, consented
mapping; none is submitted or required now.

## Decisions for v0 (2026-11-07)

These are project design decisions based on the current scope and documented
sources above, not assertions about untested filesystems or vendor products.

1. **Peer topic records.** One independent file represents one session/topic;
   each has its own stable registry ID and can reference the same opaque native
   session as another file. No canonical parent, symlink or generated alias index
   is required. This works for independent writes and offline search. Tradeoff:
   repeated native pointers and possible duplicate topics; search can show
   them and future tooling may group them without changing identity.
2. **Minimal adapter boundary.** A provider-specific adapter may supply only
   observed vendor, opaque native session, environment-neutral project
   identity, title/topic and event/time; an optional path hint is not identity.
   It calls the CLI or equivalent deterministic library, and may update only
   the intended record. Missing native ID means a visible manual fallback, not
   an invented ID. Observe start/resume and stop/end separately; leave unknown
   lifecycle state unknown. Bounded errors, unavailable roots and invalid input
   must yield warning/status without stopping the host's real work. Each adapter
   documents its actual event, input, host, trust/policy and failure semantics.
   Same-record concurrent updates and host crash recovery are not solved merely
   by using separate topic files.
3. **Filename budget.** Cap the complete initial filename, including `.md`, at
   **80 ASCII bytes**. Retain `<producer>-<short-id>-<slug>.md`; require safe
   lowercase ASCII segments, a nonempty ID component and a safe fallback slug,
   reject separators, unsafe/control characters, reserved device names and
   trailing dot/space, and handle collisions without overwriting. Final segment
   grammar and collision tests belong in the CLI fixtures. This is a conservative
   project policy, not an OS guarantee: a deep root can still exceed the total
   path limit, and a given filesystem may impose other limits. Microsoft
   documents [Windows naming](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)
   and [whole-path limits](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation).
4. **Language and packaging — owner preference not established.** The user's
   project-specific language/packaging preference is not stated in the current
   repository or available orientation notes. A reasonable *proposal* is
   Python 3 with the standard library and an installable CLI package: Python is
   available in this WSL environment and used in the neighboring
   `compliance_poc` project's documented workflows. Those facts do not prove a
   preference or Windows availability. Jim is the decision owner; confirm the
   choice when the CLI plan needs it. The research plan does not choose a
   packaging tool or require a runtime to be preinstalled everywhere.

**Still needs empirical acceptance:** Windows/WSL/RDP and sync behavior, actual
hook availability and resume, full path limits, and the necessary workplace
permissions. The WSL test plan owns these checks; unresolved evidence is not a
claim of support. The choice of storage deployment and any future MCP adapter
remain deferred.

## Remaining local verification: agent hooks

The documentation investigations above answer what the vendors describe.
Before relying on an adapter, test pre- and post-hooks across the coding agents
in use. Record evidence and test results for each agent and version; local
support is unknown until verified. Cover:

- Which pre- and post-events are available, including session, prompt, and
  tool lifecycle events, and what session or project identifiers they expose.
- Whether hooks work when the agent runs in VS Code and in its desktop UI,
  including any differences from its CLI.
- Whether each integration works on Windows and in WSL, where the hook executes,
  and how it resolves paths and the registry root in each environment.
- How hooks are configured, what happens when they fail or are interrupted,
  and whether registry updates can remain failure-open without exposing prompts
  or transcripts.

Capture the findings as an agent/version-by-interface-and-environment matrix,
with documentation links, test dates, observed limitations, and untested cases.
Use the results to choose adapter approaches; do not infer session lifecycle
events from hooks that cannot observe them.

## Related implementations reviewed

- [agents-memory](https://github.com/lolaplex/agents-memory) — Markdown-first,
  cross-agent memory implementation with session discovery ideas.
- [agent-memory-vault](https://github.com/mcncarl/agent-memory-vault) — shared
  Claude/Codex memory with Git, SQLite, and audit-oriented controls.
- [projectmem](https://github.com/riponcm/projectmem) — local event sourcing
  and deterministic projections for coding-agent memory.

These are implementation references, not endorsed dependencies. The dated
review above records licenses, observed maintenance and limits; reassess the
current license, maturity and behavior before any adoption.
