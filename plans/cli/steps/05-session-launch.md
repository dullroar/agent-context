---
id: 05-session-launch
status: pending
depends_on: [cli/05-snapshot-reads]
touches:
  - src/**
  - tests/test_cli*
  - specs/0001-filesystem-session-registry.md
  - README.md
  - plans/cli/results.md
lane: cli
gate: "manual: run offline dispatch checks and verify real-session outcomes for the target agents"
requirements: [R3, R4, R5, R6]
evidence: ""
---

# Launch a recorded session in its native agent

## Change

Add a user-invoked CLI command (for example, `agent-context resume <id>`)
that finds one record by full or unambiguous registry ID fragment and launches
its recorded native session in the corresponding CLI: Claude Code, Codex, or
GitHub Copilot. The human or agent should be able to go from a search result
to the actual session without manually reconstructing the vendor command.
Keep the deterministic registry library and existing commands useful offline;
agent hooks and setup remain in the setup plan.
Resolve registry records using the snapshot-read contract in step 05-snapshot-reads;
do not hold a registry file open during agent launch or interaction.

For each target, consult current official vendor documentation and inspect the
installed version and help, then record the documented executable, arguments,
supported environment, prerequisites and source/version. Implement only
verified command forms; a vendor name, native session ID, URL or optional
`resume` field alone is not proof that this host can reopen the session. Record
which vendor/version/host combinations are supported, unsupported, unavailable
or untested. Do not infer a successful resume from starting an executable.

## Dispatch and failure behavior

- Choose the agent from the selected record's vendor and pass its native session
  ID as one opaque argument according to that agent's verified interface. Do not
  run a command, URL, or shell fragment taken from record metadata; avoid a shell
  and handle spaces, Unicode, quotes, metacharacters and leading dashes safely.
- Reject a missing or ambiguous record, unsupported vendor, missing executable,
  malformed pointer or unsafe/unrepresentable argument with a useful nonzero
  error. Report launch failures and preserve the child's exit status where
  practical; do not silently launch a fresh or different session.
- If a registry record is unavailable and uniqueness cannot be established,
  launch nothing and explicitly report the incomplete lookup; do not return a
  nonzero exit solely because another process has the record open or denied.
- Preserve interactive terminal input, output, signals and expected exit
  behavior. Do not modify the record or change the working directory silently;
  project identity is authoritative and path hints are not automatically valid
  on this host. Document any explicit working-directory choice or prerequisite.
- Document usage, supported CLI versions and practical limits. Do not claim
  cross-machine, desktop, VS Code or vendor resume behavior until tested in the
  relevant environment. Do not read or copy session transcripts or prompts.

## Verification

Add deterministic offline tests with fake executables or subprocess isolation
for all three vendor mappings and exact argument boundaries; include session IDs
with spaces, Unicode, quotes, shell metacharacters and leading dashes; distinct
and ambiguous IDs; absent executables; unsupported vendors; malformed records;
child failure and exit behavior; and confirmation that no shell is invoked and
no registry record is changed. Test terminal handoff where practical. Run the
full offline CLI suite with local temporary controls and in a unique disposable
child of the selected Windows-profile mount; record both results separately.

For each available Claude Code, Codex and Copilot CLI, create or identify an
explicitly synthetic test session, register its observed native ID, invoke the
new command, and independently verify that the intended session opens in the
intended agent. Record agent version, host, exact procedure, observed outcome and
any human interaction; clean up only test-owned registry artifacts. Coordinate
with the WSL test plan for additional Windows/WSL and interface acceptance.
Existing authorization for this planning step does not authorize paid model
calls, changes to personal configuration, or workplace actions; follow the
[plan protocol](../../README.md) and obtain the necessary authority before such
operations. If an agent, account, supported resume mechanism or required
permission is unavailable, record that check as blocked or untested and
escalate the concrete decision; a fake-process test or a newly opened session is
not proof of a real resume.

## Dependencies and completion

Start only when the listed prerequisite is done with evidence. Work within the
owned paths, preserve existing files and completed baseline evidence, and update
specification and results when commitments change. Set `status: done` only after
the implementation, full offline suite and real-session checks pass for the
required targets; otherwise record the specific escalation and leave the step
incomplete. Include exact commands, dates, environments and limitations in the
step evidence and `plans/cli/results.md`.
