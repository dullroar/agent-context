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

## CLI

Python 3.10 or newer and the common PyYAML package are required. From this
checkout, install the CLI with:

```bash
python -m pip install .
```

After installation the CLI works offline. `AGENT_CONTEXT_HOME`, when set,
selects the registry root. Otherwise it uses `~/.local/share/agent-context` on
Linux/WSL and `%LOCALAPPDATA%\agent-context` on Windows (or the user home
if `LOCALAPPDATA` is unset). Every command prints its resolved root to standard
error; Windows and WSL roots are separate unless explicitly configured to the
same accessible location. A project identity is portable; paths are optional
hints. For a shared Windows-profile test root see the
[plan protocol](plans/README.md#shared-windowswsl-test-location).

```bash
agent-context register --producer codex --vendor codex \
  --session "opaque session id" --project "git:https://example.org/team/repo.git" \
  --title "Loan validation" --status active
agent-context list
agent-context search "loan"
agent-context show acr_0123456789ab
agent-context validate
```

Use the ID returned by `register` with `show`; an unambiguous ID fragment also
works. Run `agent-context register --help` for optional path hints and notes.
The CLI returns zero when it finds no invalid records or operation errors,
one for invalid records or operation errors, and two for command-line usage
errors. List, search and validate report invalid
records rather than silently treating them as valid. Direct write failures are
nonzero: a calling adapter must handle them without blocking the host agent.
New records require same-directory hard-link support; unsupported filesystems
produce an error instead of risking an overwrite or incomplete visible record.

Readers take a private in-memory snapshot and release the source file before
parsing. They do not request registry locks. On Windows they permit compatible
read, write and delete sharing. If a file is unavailable because of a sharing
conflict, denied permission, or disappearance during a scan, list and search
warn and continue with other records; a warning can therefore indicate a
persistent access problem, not only a temporary lock. Validation reports an
unavailable count, and show emits no record when it cannot establish uniqueness.
Those cases return zero if there is no other error, so scripts must inspect
warnings and output for completeness rather than rely on exit status alone.
An external exclusive lock, permissions, an interrupted in-place write or a
network filesystem can still prevent or delay a read. A snapshot is not a way
to bypass such restrictions.

Run the offline tests from a checkout where PyYAML is installed:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The registry stores pointers, not transcripts. Do not put secrets or prompt
contents into records. Vendor IDs are opaque and recording one does not imply
that the vendor supports resume.

## Status

The reference CLI has passed its offline acceptance suite on local storage and
the selected Windows-profile WSL mount. Adapter setup and cross-interface
Windows/WSL agent acceptance are separate planned work.
