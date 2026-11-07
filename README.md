# agent-context

**Personal research:** This repository is Jim Lehmer's personal research.
It explores ideas and possible designs; I may or may not implement them.

A local-first, filesystem-native registry for finding the *conversation or
agent session that did the work*, across coding-agent vendors and machines.

The proposed implementation has a narrow goal: create and search portable
session pointer records without requiring a daemon, database, MCP server, or
access to the original transcript. It is not a competing universal memory
standard.

## Problem

Vendor-native chat titles and session IDs are poor human discovery keys. A
project can have many sessions with the same generic prompt but materially
different outcomes. The human needs a durable answer to: "where was that
conversation about that thing?"

## v0 scope

- One independent, filesystem-visible record per session/topic.
- Stable identity plus short, human-recognizable subject slug.
- A pointer to the vendor-native session or transcript, not a copied transcript.
- Git-friendly, Markdown-first records and deterministic local search.
- Failure-open adapters: registry recording must never block normal agent work.

Out of scope for v0: transcript migration, semantic memory retrieval, a cloud
service, distributed locking, or a new runtime protocol.

## Start here

- [Design](DESIGN.md) — architecture and explicit non-goals.
- [Interoperability research](RESEARCH.md) — adjacent standards and gaps.
- [Initial protocol spec](specs/0001-filesystem-session-registry.md).
- [Coordinated plans](plans/README.md) — research, CLI, setup, and WSL testing.
- [Repository memory](MEMORY.md) — accumulated operational findings.

## Status

Planning and specification. No implementation exists yet.
