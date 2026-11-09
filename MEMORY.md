# Repository memory

Non-obvious findings about this codebase and its operating environment,
discovered during work but not designed for anywhere else — not in README.md
(what it is and how to use it), DESIGN.md (architectural decisions), or
AGENTS.md (operating rules). Keep entries factual and dated.

## Findings

- 2026-11-08 — In disposable WSL CLI tests with synthetic providers confined
  to a loopback-only network namespace, Codex 0.157.0, Claude Code 2.1.319 and
  Copilot CLI 1.0.107 emitted session-start and session-end events with IDs
  present. In the tested noninteractive output modes, forcibly terminating or
  timing out a raw hook did not produce an observable hook warning in captured
  CLI output, although the synthetic turn continued. A per-launch monitor
  subsequently reported marked hook termination and timeout in synthetic
  end-to-end tests. This does not establish behavior for authenticated
  services, Windows-native agents or other UIs.
- 2026-11-07 — On the selected Windows-profile filesystem with Windows Python
  3.14.4, a normal Python reader prevented `os.replace` while open. A reader
  explicitly sharing read/write/delete plus a writer using Windows POSIX-style
  replacement allowed an independent writer to replace the file while the
  reader finished the old snapshot. An exclusively opened writer denied both
  Python and Windows `TYPE`; the reader cannot bypass that sharing policy.
  WSL `cat` also received permission denied for an exclusively opened Windows
  file; WSL `less` returned no record and, in one probe, exit zero. The tested
  mount is not evidence about network shares or other filesystems.
- 2026-11-06 — The name "Open Memory Protocol" is used by multiple unrelated
  projects. When referring to the IBM/Mozilla co-convened effort, use its
  organization or canonical repository URL rather than the acronym alone.
- 2026-11-06 — The first validated gap is human session discovery via
  local, vendor-native pointers. It is narrower than portable memory and is
  intentionally viable without a daemon, database, or MCP server.
