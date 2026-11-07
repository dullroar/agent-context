# Design

## Boundary

`agent-context` is a local session-discovery layer. It records *where work was
discussed or performed*, not the full reasoning, transcript, or long-term
knowledge derived from it.

## Architectural position

```text
Human discovery
  -> session registry (this project)
  -> vendor-native session / transcript

Task context
  -> portable memory protocol or project Markdown
  -> agent runtime

Tool access and remote collaboration
  -> MCP / A2A
```

These layers may link to one another but must not be conflated. In particular,
MCP can expose this registry later; it is not the registry's data model.

## Core decisions

- **Filesystem first:** records are ordinary files; directory listing is the
  minimum viable index.
- **Identity before title:** a stable record ID prevents a changed topic label
  from changing the session's identity.
- **Short paths:** keep portable filenames short to reduce Windows path risk.
- **Environment-neutral identity:** project and session identity must not depend
  on an absolute Windows or WSL path. Environment-specific locations are
  optional hints, never the sole locator.
- **Append-friendly:** agents write separate records; no shared mutable central
  index is required for normal registration.
- **Pointers, not copies:** native vendor session references stay authoritative.
- **Deterministic base:** creation, validation, filename derivation, and search
  must work without model inference. An LLM may propose a human-friendly slug.
- **Failure open:** inability to record or enrich a pointer cannot stop an agent.

## Storage root

The protocol will resolve `AGENT_CONTEXT_HOME` first. If it is unset, the
reference implementation will choose a platform-appropriate local default and
display it explicitly. The repository will not prescribe a roaming-profile
location: enterprise profile and sync behavior must remain a deployment choice.

## Windows and WSL

The same repository may be opened by Windows-native and WSL-native agents.
The record format therefore stores an environment-neutral project identity
(normally a Git remote plus repository-relative path) separately from optional
path hints. A path that works in `C:\\Users\\...` must not be assumed valid in
`/mnt/c/...`, and the reverse is equally true. The reference CLI will report
which registry root it resolved rather than silently crossing the Windows/WSL
boundary.

## Provenance

Each record may carry created/updated timestamps, producer, project locator,
and evidence links. Git history is the preferred provenance mechanism when the
registry root is versioned. Cryptographic provenance is an optional future
integration, not a v0 dependency.

## Non-goals

- Reopen a foreign vendor session as though it were native.
- Resolve concurrent cloud-sync conflicts as a distributed transaction system.
- Standardize all agent memory, identity, authorization, or task orchestration.
- Require MCP, A2A, SQLite, embeddings, or an always-on service.
