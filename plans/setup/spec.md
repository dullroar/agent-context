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
- **R6 — One installer per shell:** provide both `scripts/setup.sh` for Bash
  on WSL/Linux and `scripts/setup.ps1` for PowerShell on Windows. A normal
  interactive run asks exactly one question: **Where does the registry go?**
  It may accept the same path as an explicit argument for unattended use.
  Resolve and display the selected root, then verify directory access with a
  disposable, uniquely named write/read/delete probe before making any agent
  configuration changes. If the root cannot be used, stop with a clear error
  and no agent installation; do not silently select a different root. The
  selected directory may be created if absent, without overwriting existing data.
- **R7 — Detect and configure all three agents:** each installer checks for
  Codex, Claude Code and GitHub Copilot independently in its own execution
  environment. For each detected agent, install the corresponding supported
  pre/post hooks, wrappers, instructions, or other integration artifacts into
  that agent's appropriate locations, and configure the chosen root through
  the verified mechanism for that host. Artifacts and locations may differ by
  agent. Preserve unrelated settings and hooks; make managed changes visible,
  repeatable and reversible, and never silently overwrite user modifications.
  Report installed, absent, unsupported and failed cases separately, including
  any manual step. An unavailable or unverified integration is not a success.
  Detect Windows and WSL installations separately; an executable or shim on
  `PATH` alone does not prove a working CLI or another interface's support.

For R6–R7, tests must cover all three agents present individually and together,
none present, a nonfunctional shim, path quoting and spaces, missing or denied
roots, failed probes, safe cleanup, existing configurations, reruns and a
per-agent failure after successful preflight. A failed root preflight must leave
all agent settings and integrations untouched. Validate both installer entry
points in their actual shell/OS or record the unavailable check as blocked.
Explicitly running an installer to configure the current user authorizes its
documented changes for that environment; it does not authorize changes to
workplace policy or another user's configuration.

## Boundaries and validation

Honor the CLI/spec design and do not require a daemon, MCP, model or network.
Per-agent controls may prohibit or supersede user-level hooks; record limits,
not workarounds. Run offline integration tests and the complete CLI suite after
integration, then follow the WSL acceptance plan. Record exact commands,
environment, observed results and gaps. Escalate genuine scope/permission
conflicts or protected checks that cannot pass, not ordinary implementation
failures. Workplace configuration and cross-boundary data transfer require
applicable authorization and policy review before use.
