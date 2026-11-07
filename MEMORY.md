# Repository memory

Non-obvious findings about this codebase and its operating environment,
discovered during work but not designed for anywhere else — not in README.md
(what it is and how to use it), DESIGN.md (architectural decisions), or
AGENTS.md (operating rules). Keep entries factual and dated.

## Findings

- 2026-11-06 — The name "Open Memory Protocol" is used by multiple unrelated
  projects. When referring to the IBM/Mozilla co-convened effort, use its
  organization or canonical repository URL rather than the acronym alone.
- 2026-11-06 — The first validated gap is human session discovery via
  local, vendor-native pointers. It is narrower than portable memory and is
  intentionally viable without a daemon, database, or MCP server.
