# 0001 — Filesystem session registry

Status: draft  
Date: 2026-11-06

## Intent

Define the smallest portable record that lets a human and a program find a
vendor-native agent session by project, subject, producer, or time.

## Record model

One UTF-8 Markdown file represents one `session-topic` pointer. Multiple files
may legitimately point to the same native session when it covers distinct work.
They are peer records with distinct stable IDs; no canonical parent, alias
symlink or generated index is required.

Required front matter:

```yaml
id: acr_01J...
native:
  vendor: codex
  session: "opaque-vendor-session-id"
project:
  identity: "git:https://example.invalid/org/repo.git"
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
lowercase ASCII `slug` is descriptive but non-authoritative. The complete filename, including `.md`, is limited to 80 ASCII bytes. Use
safe lowercase ASCII segments and a nonempty short ID, with a safe fallback
slug; reject separators, unsafe/control characters, reserved Windows device
names and trailing dots or spaces. Resolve collisions without overwriting.
This component budget does not guarantee that the entire path fits every
filesystem. The CLI fixtures will define exact segment grammar and test it.

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

## Adapter contract and deferred decisions

A vendor adapter supplies only an observed opaque native session ID, vendor,
project identity, topic/title and observed event/time, with optional path hints.
It invokes the deterministic registry and handles failure without blocking the
agent. If a native ID is unavailable, use a manual fallback; never manufacture
one. A turn stop is not necessarily session end. Unsupported or unobserved
lifecycle transitions remain `unknown`, with the precise event recorded by the
adapter. Hooks, resume and write behavior need environment-specific testing.

Language and packaging remain an owner decision; see [research](../RESEARCH.md).
Storage deployment and any optional MCP adapter are deferred.
