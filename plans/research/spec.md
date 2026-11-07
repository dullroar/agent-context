# Research — specification

Status: complete — research review and documentation, 2026-11-07. Runtime
acceptance, workplace access and the CLI language decision remain downstream
work and are not claimed as verified.

## Outcome

Turn the open investigations in [RESEARCH.md](../../RESEARCH.md) into dated,
source-backed answers that inform the CLI, setup, and test plans. Begin with
GitHub Copilot and the actual desktop/VM workflows. Findings are evidence, not
claims that a particular local installation works.

## Requirements and protected checks

- **R1 — Copilot first:** compare VS Code Copilot agent modes, CLI, desktop and
  any remote/cloud modes actually available; include event names, native IDs,
  configuration, execution host and Windows/WSL support. Mark version-dependent
  or untested combinations unknown. Check official documentation and record
  policy or enterprise limitations.
- **R2 — Agent integration:** apply the same matrix to Claude and Codex CLI,
  VS Code and desktop experiences; verify start, resume, prompt, tool, stop and
  end events separately, identifier availability, error/timeout behavior and
  privacy. Distinguish documented claims from local observations.
- **R3 — Shared storage:** evaluate local Windows, WSL, RDP redirected drive
  (including `\\tsclient\C\Users\<username>\ai-dist-mem`), network share and
  sync-folder options. For each record identity, permissions/policy,
  availability, concurrency, replace/rename, interruption, conflict and
  recovery assumptions; do not assert network rename is atomic without tests.
- **R4 — Prior work and decisions:** revisit existing standards and all three
  linked implementation references, including license and current maturity;
  resolve or record owner-needed decisions for spec 0001's open questions,
  filename budget, language and packaging. Only propose upstream work if useful.
- **R5 — Durable evidence:** after each investigation update RESEARCH.md with
  answer, source links, version/date, tested environment, evidence and explicit
  unknowns; revise DESIGN.md/spec only when an actual decision changes them.

## Constraints and execution

Prefer primary vendor and platform sources, preserve findings with links and
access dates, and do not invent capabilities or native resume support. Parallel
research can gather notes, but RESEARCH.md is a shared output: integrate it
serially. Do not gather prompts or transcripts, change employer policy or assume
permission to move workplace data. Available research is not evidence of local
execution. Record decisions and outstanding questions, with owner if known.

Combined validation: inspect RESEARCH.md for answers and evidence against R1–R5,
check all new local links, and confirm remaining unknowns are explicit. Record
per-step evidence. Escalate only a decision needed to proceed, unavailable
permission, or an acceptance check that cannot be satisfied; do not label an
untested environment as passing.

## Completion evidence

On 2026-11-07, the five step records were checked against R1–R5 and the linked
research sections: Copilot interfaces and lifecycle; Claude and Codex hooks;
shared-root topology; implementation and protocol crosswalk; and v0 decisions.
The check distinguished documentation from local executable version observations
and explicitly marked untested sessions, hooks, filesystem behavior, desktop,
VM, policy and resume. The language and packaging preference is recorded as an
owner-needed decision for CLI work, as R4 permits.

A local Python structural check validated all 18 step metadata records, the
dependency graph and links in 32 Markdown files; `git diff --check` passed.
These checks verify document structure, not vendor or platform behavior.
