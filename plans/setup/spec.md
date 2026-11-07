# Setup — specification

Status: proposed

## Outcome

Make the registry usable by agents and humans: provide reproducible setup and
teardown scripts, explicit instructions, and evidence-based integration choices
for each available agent environment. Use research findings, not assumed hooks.

## Requirements and protected checks

- **R1 — Portable setup:** agent-runnable scripts offer inspection, explicit
  install/configure and reversal or dry-run where feasible; preserve existing
  user settings and never overwrite hooks silently. Document prerequisites,
  root choice, installation, update, uninstall and troubleshooting for humans.
  Do not change a user's global config until authorized for that environment.
- **R2 — Layered adoption:** compare deterministic hooks/wrappers, concise
  AGENTS.md/CLAUDE.md (and Copilot-specific instructions if supported), and
  skills for discovery and procedure. Recommend both when each has a job:
  hooks automate observed events, instructions tell agents when to use the
  registry, skills provide an optional reusable workflow where supported.
  At the start of relevant work, guide the agent to search for prior sessions;
  when useful work is recorded, guide it to register or update a pointer using
  only identifiers actually available. Do not assume either action was done.
  Avoid assuming skills auto-load or that repeated instructions enforce use.
- **R3 — Honest lifecycle:** implement and document only verified integration
  points for supported CLI/VS Code/desktop combinations. Report actual event,
  runtime host and available identifiers; never invent native session IDs,
  session-end events or resumability. Document a manual fallback and explicit
  `unknown` state where needed.
- **R4 — Failure open:** registry failure, missing root, timeout or interrupted
  hook yields bounded warning/status without denying normal agent work; do not
  turn a registry integration into a blocking pre-tool policy. Verify provider
  failure behavior including timeout, exit code and hook JSON if relevant.
  Never log prompt/transcript/secret content by default.
- **R5 — Tests and handoff:** offline tests exercise configuration merging,
  repeated setup, no-clobber, reversal, argument quoting/spaces, missing CLI,
  simulated write failures and hook event handling. Provide copy-paste examples
  and a matrix identifying supported, manual, unavailable and untested paths.

## Boundaries and validation

Honor the CLI/spec design and do not require a daemon, MCP, model or network.
Per-agent controls may prohibit or supersede user-level hooks; record limits,
not workarounds. Run offline integration tests and the complete CLI suite after
integration, then follow the WSL acceptance plan. Record exact commands,
environment, observed results and gaps. Escalate genuine scope/permission
conflicts or protected checks that cannot pass, not ordinary implementation
failures. Workplace configuration and cross-boundary data transfer require
applicable authorization and policy review before use.
