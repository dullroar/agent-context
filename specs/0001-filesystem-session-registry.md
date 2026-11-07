# 0001 — Filesystem session registry

Status: draft  
Date: 2026-11-06

## Intent

Define the smallest portable record that lets a human and a program find a
vendor-native agent session by project, subject, producer, or time.

## Record model

One UTF-8 Markdown file represents one `session-topic` pointer. Multiple files
may legitimately point to the same native session when it covers distinct work.

Required front matter:

```yaml
id: acr_01J...
native:
  vendor: codex
  session: "opaque-vendor-session-id"
project:
  identity: "git:https://example.invalid/org/repo.git#main"
title: "loans2 null validation"
created_at: "2026-11-06T20:00:00Z"
status: active
```

Optional fields: `machine`, `path_hints`, `resume`, `updated_at`, `tags`,
`otel_trace_id`, `a2a_context_id`, `evidence`, and `supersedes`. `path_hints`
may be keyed by `windows` or `wsl`, but are convenience data only. `project`
identity is preferred over an absolute path so the same repository remains
recognizable from both environments.

The body is a short human note. It must never require a transcript.

## File naming

Canonical initial filename:

```text
<producer>-<short-id>-<slug>.md
```

`producer` is a short agent/machine label; `short-id` is derived from `id`; the
lowercase ASCII `slug` is descriptive but non-authoritative. The implementation
will define a conservative maximum filename length and reject unsafe characters.

Renaming changes only discovery text. `id` and `native.session` remain stable.

## Lifecycle

`active`, `paused`, `completed`, `abandoned`, and `unknown` are local registry
states. They express the pointer's last known state, not a claim about the
vendor's canonical state. Updates must use replace/rename semantics where the
filesystem supports them. A stale record is preferable to a missing record.

## Safety and portability

- Treat every native locator as untrusted opaque data.
- Do not store secrets, transcript contents, or prompt text by default.
- Resolve the registry root through `AGENT_CONTEXT_HOME` before platform
  defaults.
- Never require a Windows path to be usable from WSL, or a WSL path to be
  usable from Windows. Store both as optional hints when they are known.
- The record is valid without Git, MCP, A2A, or network access.

## Open questions

1. Should one native session have a stable canonical pointer file plus topic
   aliases, or should every topic file be a peer record?
2. What minimal vendor adapter contract can create and update records without
   claiming lifecycle hooks that do not exist?
3. What exact cross-platform filename budget is safe enough to document?
