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
id: acr_0123456789abcdef0123456789abcdef
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
filesystem. The reference CLI contract below defines exact segment grammar.

Renaming changes only discovery text. `id` and `native.session` remain stable.

## Lifecycle

`active`, `paused`, `completed`, `abandoned`, and `unknown` are local registry
states. They express the pointer's last known state, not a claim about the
vendor's canonical state. Updates must use replace/rename semantics where the
filesystem supports them. A stale record is preferable to a missing record.

An active agent is the sole intended writer of its registry pointer. Readers
enumerate and take a private byte snapshot without requesting an application
lock, close the source, then parse the snapshot. This is a protocol convention,
not enforcement against another writer. Snapshot reads still open the original:
Windows sharing restrictions, filesystem locks and permissions can prevent
access, and arbitrary filesystem I/O cannot be guaranteed not to block. A
snapshot copied during an in-place write can be incomplete. Writers should
publish complete replacements; readers validate what they actually read.

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

Jim selected Python 3 and a simple installable CLI on 2026-11-07. The reference
implementation uses the widely used PyYAML package to read and write YAML;
record operations and the test suite require no network, model, daemon or service.
Storage deployment and any optional MCP adapter are deferred.


## Reference CLI contract

Records use YAML front matter between lines containing only `---`, followed by
an optional UTF-8 Markdown body. Metadata is a mapping; duplicate keys, YAML
aliases, unknown fields, malformed UTF-8 and malformed front matter are invalid.
Strings must be nonempty and contain no control characters, except body text may
contain newlines and tabs. Quote values such as opaque identifiers when needed
to keep them YAML strings. The CLI preserves opaque vendor and session values.

- `id`: `acr_` followed by 32 lowercase hexadecimal digits (UUID4-derived).
- `native`: mapping with exactly string keys `vendor` and `session`.
- `project`: mapping with exactly string key `identity`. Identity cannot be an
  absolute POSIX or Windows path or a `file:` URL; path hints are not identity.
- `title`: string; `created_at`: ISO 8601 timestamp with timezone, parsed as a
  string (quoting is recommended for interoperability with other YAML tools).
- `status`: one of `active`, `paused`, `completed`, `abandoned`, `unknown`.
- Optional `machine`, `resume`, `otel_trace_id`, `a2a_context_id`, and
  `supersedes` are strings. `updated_at` is a timezone-aware ISO 8601 timestamp.
  `path_hints` is a nonempty mapping of `windows` and/or `wsl` to strings;
  `tags` and `evidence` are lists of nonempty strings. Unknown keys are invalid.

Initial filenames are at most 80 ASCII bytes including `.md`. The producer is
1–24 lowercase ASCII letters or digits, with single internal hyphens permitted;
its entire value cannot be a Windows device name (`con`, `prn`, `aux`, `nul`,
`com1`–`com9`, or `lpt1`–`lpt9`). The short ID is the first 12 hexadecimal
digits of the record ID. The title slug is lowercase ASCII letters and digits
separated by single hyphens, truncated to fit and stripped of trailing hyphens;
if no ASCII letters or digits remain, use `topic`. The filename is
`<producer>-<short-id>-<slug>.md`. Reject separators, control characters,
trailing dots/spaces, Windows device filenames and other noncanonical names.
Creation writes and flushes a same-directory temporary file, then publishes it
with an exclusive hard link, retrying with a fresh ID on collision. Registration
fails visibly if the filesystem does not support this operation. It never
overwrites an existing record; updates, if used, write a same-directory temporary
file and replace the target. On Windows the reference writer uses POSIX-style
replacement where supported, otherwise it falls back to ordinary replacement,
which may fail while a reader is open. Link and replacement semantics are not
assumed on untested network filesystems. A crash can leave a hidden temporary file.

The reference CLI implements `register`, `list`, `search`, `show` and
`validate`. Search is case-insensitive substring matching over title, project
identity, vendor and registry ID. `show` accepts a full ID or unambiguous ID
fragment; ambiguous or missing IDs fail. Listing and search report invalid
records and exit nonzero rather than silently hiding corruption. A file that
cannot be read because of a sharing conflict, denied permission, or disappearance
during a scan is reported as unavailable with a warning, and does not by itself
make list or search fail. A permission error does not establish whether a lock
or filesystem permissions caused it. Validation reports unavailable records
without marking them valid, and show emits no record if it cannot establish
uniqueness. Both warn but return zero if unavailability is the only issue; a
zero exit therefore does not establish that a scan or lookup was complete.
Registry scans
inspect non-hidden files in the root and report invalid filenames or content;
directories and hidden files are ignored. Each command
reports the resolved root. `AGENT_CONTEXT_HOME`, when set to a nonempty value,
takes precedence; otherwise the default is `LOCALAPPDATA/agent-context` on
Windows (falling back to the user home) and `~/.local/share/agent-context`
on other platforms. The root is local to the running environment. A direct
write failure is nonzero; callers implementing failure-open behavior handle it.

Fixtures in `tests/fixtures/` define representative valid and invalid metadata
and filename cases. The test suite supports `AGENT_CONTEXT_TEST_PARENT` to run
filesystem tests in unique temporary children of a chosen existing directory;
the default uses ordinary local temporary directories.
