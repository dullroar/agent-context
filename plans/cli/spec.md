# CLI — specification

Status: snapshot-read extension verified and session-launch extension planned;
the initial CLI passed R1–R5 on
2026-11-07. See [acceptance results](results.md) for that baseline and its
platform limitations. This plan succeeds the former 0001-foundation plan.

## Outcome and boundary

Deliver an offline, local CLI that creates, validates, lists, searches and shows
session-pointer records conforming to [spec 0001](../../specs/0001-filesystem-session-registry.md),
and can launch a recorded session with the appropriate supported agent CLI.
It is not a transcript store, memory graph, daemon, database, MCP requirement,
or universal agent runtime. Adapters and setup belong to the setup plan;
Windows/WSL and multi-interface acceptance belongs to wsl-test.

## Requirements and protected checks

- **R1 — Decisions and fixtures:** resolve the three open spec questions and
  choose language/packaging using documented tooling preferences and research;
  freeze positive and negative fixtures, filename budget, lifecycle vocabulary
  and schema. A machine-readable schema is optional if it duplicates the spec.
- **R2 — Deterministic core:** resolve `AGENT_CONTEXT_HOME` then explicit local
  default, display resolved root, generate stable IDs and safe short filenames,
  parse/validate UTF-8 metadata, and write via safe replacement where supported.
  Never assume replacement semantics on an untested network filesystem.
- **R3 — CLI:** `register`, `list`, `search`, `show`, `validate`; registration
  accepts opaque vendor/session values offline, supports multiple topics per
  native session, and avoids shared indexes and accidental overwrites. Search
  covers title, project, vendor and ID fragment.
- **R4 — Portability and failure:** malformed metadata and unsafe filenames are
  rejected; paths with spaces and UTF-8 work; simulated write failure returns
  nonzero and preserves existing valid data. Independent concurrent creates do
  not overwrite. Environment-neutral project identity remains authoritative;
  Windows and WSL paths are optional hints. Never silently cross roots.
- **R5 — Verification:** meaningful tests cover every schema, filename,
  validation and search rule; full suite runs offline without a model, service,
  daemon or network. Record the actual commands and results.
- **R6 — Launch a recorded session:** add a user-invoked command that resolves a
  record by full or unambiguous partial registry ID and uses its recorded vendor
  and opaque native session ID to launch that session with the matching Claude
  Code, Codex or GitHub Copilot CLI, using each vendor's documented, verified
  resume mechanism. Preserve interactive terminal behavior and report missing
  agents, ambiguous IDs, unsupported vendors, unavailable sessions and child
  failures clearly. Do not interpret metadata as shell code or assume a session
  is available on another host. Offline tests must verify safe dispatch and
  failures without launching an agent; real-session tests must independently
  verify the correct session and agent, with unavailable checks recorded as
  blocked/untested rather than passed. See [step 05](steps/05-session-launch.md).
- **R7 — Nonexclusive snapshot reads:** registry pointer records belong to one
  active agent/writer. Readers do not request a lock or retain a source handle
  while interpreting a record; take a private snapshot first. On Windows, share
  read, write and delete access so our short-lived read handle does not prevent
  a cooperative writer from updating or replacing its file. A denied read or
  platform-enforced lock cannot be bypassed by copying; report an unavailable
  record without claiming it was read or validated. Directory scans and other
  readable records should remain usable when an individual record is busy;
  unavailability alone must not cause a nonzero exit. An explicit incomplete
  status or warning must distinguish this from a complete result.
  Never claim external agents or filesystems guarantee lock-free access without
  testing. See [snapshot step](steps/05-snapshot-reads.md).

The previous foundation plan's adapter investigation, platform acceptance and
interoperability review are retained in research, setup and wsl-test. The CLI
must expose enough deterministic status and errors for failure-open wrappers;
a direct CLI write failure still returns nonzero.

Starting with the core filesystem tests, the user's selected Windows-profile
`ai-dist-mem` mount is a required test target, using a unique disposable child
directory as specified in [the plan protocol](../README.md#shared-windowswsl-test-location).
Test local temporary controls too. Verify and report the mounted-root outcome
separately; an inaccessible mount is blocked, not a pass. This test selection
does not change the product's unspecified platform default, require Windows
for offline CLI operation, or make an absolute path the project identity.

## Execution and authority

Keep the v0 boundary and [repository rules](../../AGENTS.md). Work within the
step-owned paths; update design/spec when commitments change. Protected checks
above may not be weakened, skipped or deleted to obtain a pass. Select a
reasonable language only after reviewing recorded preferences; ask for a decision
if those preferences are unavailable and the choice cannot be made in scope.
The baseline and automated suite need no live model calls. Launching a real
agent may use an authenticated service or incur charges; obtain any authority
required by the plan protocol before such a test. Integrate lanes and run the full offline suite;
record commands, environment, date, result and limitations. Escalate a genuine
scope conflict, missing authority or protected check that cannot pass.
