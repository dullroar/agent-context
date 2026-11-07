# Instructions for agents working in this repository

## Project boundary

Implement a local-first session registry. Do not silently expand the project
into a transcript store, a vector-memory system, an MCP server, or a universal
agent runtime.

## Working rules

- Read `DESIGN.md`, the active specification in `specs/`, and the relevant plan
  in `plans/` before changing behavior. Follow [the plan execution protocol](plans/README.md)
  for dependencies, parallel file ownership, integration, and evidence.
- Keep v0 dependency-free where practical. A CLI must function without network
  access, a daemon, or a model call.
- Preserve failure-open behavior: registration and enrichment failures must
  yield a useful warning/status, not prevent the caller's real work.
- Treat vendor session IDs and URLs as opaque strings. Never claim a pointer is
  resumable without testing that vendor's supported mechanism.
- Maintain short, Windows-safe paths and filenames. Test behavior on paths with
  spaces and use explicit UTF-8 text handling.
- Add test cases for every schema, filename, validation, or search rule.
- Record a durable non-obvious finding in `MEMORY.md`; put design decisions in
  `DESIGN.md` or a spec instead.

## Change discipline

Update the relevant specification and plan when their commitments change. Do
not introduce generated indexes or a central lock file unless a design record
explicitly justifies the tradeoff.
