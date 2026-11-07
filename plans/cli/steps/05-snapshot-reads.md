---
id: 05-snapshot-reads
status: done
depends_on: [cli/04-integration]
touches:
  - DESIGN.md
  - MEMORY.md
  - specs/0001-filesystem-session-registry.md
  - src/**
  - tests/test_core*
  - tests/test_cli*
  - README.md
  - plans/cli/results.md
lane: cli
gate: "manual: exercise lockless snapshot reads and platform-specific sharing behavior"
requirements: [R2, R3, R4, R5, R7]
evidence: "2026-11-07: full suite discovered 20 tests; local WSL passed 17 with 3 platform-specific skips, mounted WSL passed 18 with 2 Windows-only skips and cross-host comparison enabled, and Windows Python 3.14.4 passed 17 with 3 WSL/POSIX skips. The skipped checks were run on the other platform. Windows-native reader and independent writer, Windows TYPE, WSL cat/less, and an exclusive Windows writer against WSL readers were exercised. Exclusive access cannot be bypassed and the CLI reports incomplete results without nonzero exit for unavailability alone. Exact commands, prior failed ordinary-replace check and limitations are in ../results.md."
---

# Read registry pointers through nonexclusive snapshots

## Change

A live agent owns its registry pointer for writing; other actors discover names
without taking locks and read a private snapshot before interpreting metadata.
Do not acquire reader or central locks. Close the source immediately after the
copy; an in-memory byte snapshot is equivalent to a uniquely named, promptly
cleaned up temporary copy and avoids leaving metadata on disk. A reader must not
hold a registry handle during parsing, search, display or session launch. Treat
single-writer ownership as a protocol rule; do not claim enforcement against
uncooperative processes or control over a vendor's native session files.

On Windows, open the source read-only with read/write/delete sharing enabled so
our read handle does not itself prohibit a writer from writing or replacing the
record. Other agents and the operating system can still deny the initial open
or later reads. Do not wait on, force, break or work around another process's
lock. An inaccessible record is unavailable, not a valid snapshot; preserve
clear diagnostics, allow independent readable records to be listed/searched,
and return zero when unavailability is the only issue. A validation reports
unavailable counts and a lookup that cannot establish uniqueness emits no record
and an explicit warning. A zero exit in these cases is not proof of completeness.
A copy during an in-place write is not inherently consistent. Cooperating writers
should publish complete records via the existing replacement strategy; validate
snapshot content and never assume untested filesystem semantics.

## Verification

Test that the original handle is closed before parsing and no reader locks are
requested. On Linux compare `cat`, `less` and the CLI while a writer holds an
advisory exclusive lock, using timeouts. On Windows compare `TYPE` and the CLI
with sharing and exclusive writers; test WSL readers against an exclusive
Windows writer on the shared mount. On Windows-native Python exercise a reader concurrently
with a sharing writer and replacement, and separately show that a writer that
forbids sharing causes a visible unavailable result. Exercise registry scans,
lookup and validation with busy, invalid and valid records, preserving other
records and reporting incomplete results honestly. Run the full offline suite
locally and in a unique child of the selected mounted test base. Record commands,
platforms and cleanup; a missing Windows-native check is blocked, not a pass.
Do not claim a hard timeout for arbitrary network filesystem I/O or that snapshots
can defeat OS-enforced sharing restrictions.

## Completion and record

Honor the listed dependency and file ownership, preserve existing plan evidence,
and update the design/spec when commitments change. Record exact commands,
environment, date, results and limitations in this step and `plans/cli/results.md`.
Mark done only when the required checks actually pass; otherwise leave the step
incomplete and record the specific limitation.
