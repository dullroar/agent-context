# 0001 — Foundation plan

Status: proposed  
Date: 2026-11-06

## Outcome

A small local CLI can create, validate, list, and search session-pointer records
conforming to spec 0001, with no service dependency.

## Sequenced implementation steps

1. **Decision closure** — resolve the three open questions in spec 0001; choose
   a language and packaging model only after checking the user's existing
   tooling preferences.
2. **Schema and fixtures** — freeze an example record set, filename grammar,
   lifecycle vocabulary, and negative validation cases. Add a machine-readable
   schema only if it does not duplicate the human-facing spec.
3. **Core library** — implement root resolution, ID generation, safe filename
   derivation, atomic write/rename, front-matter parsing, and validation.
4. **CLI** — implement `register`, `list`, `search`, `show`, and `validate`.
   `register` must work with opaque vendor/session arguments and must not
   contact an external service.
5. **Adapters** — investigate agent pre- and post-hook support across VS Code,
   desktop UIs, Windows, and WSL as described in `RESEARCH.md`, then prototype
   one wrapper or hook per available coding-agent environment. Each adapter
   must declare exactly which lifecycle event it can observe; unsupported events
   remain `unknown` rather than being guessed.
6. **Windows/WSL acceptance** — test the same Git checkout registered from
   Windows and WSL; spaces, long-but-valid paths, interrupted writes,
   concurrent independent registration, and sync-folder behavior. Confirm that
   path hints do not replace environment-neutral project identity and that root
   selection never silently crosses the Windows/WSL boundary.
7. **Interoperability review** — map optional fields to OpenTelemetry, A2A, and
   portable-memory work; decide whether to propose a contribution upstream or
   keep this as a narrow implementation.

## Acceptance checks for the first implementation slice

- A user can register two topic records for one opaque native session without a
  shared index or overwrite.
- `search` finds records by title, project, vendor, and ID fragment.
- Validation rejects unsafe filenames and malformed required metadata.
- A simulated write failure returns nonzero status without damaging an existing
  valid record.
- The same Git project registered from Windows and WSL has one recognizable
  project identity even when its absolute paths differ.
- The complete test suite runs offline.

## Deferred decisions

- Whether records live in a Git repository, a sync folder, or both.
- Whether topic aliases are symlinks, peer files, or a later index feature.
- Whether any MCP server should be built after the CLI.
