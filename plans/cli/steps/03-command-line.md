---
id: 03-command-line
status: pending
depends_on: [cli/02-core]
touches:
  - src/**
  - tests/test_cli*
  - pyproject.toml
  - README.md
lane: cli
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R3, R4, R5]
evidence: ""
---

# Expose the registry CLI

## Change

Build register, list, search, show and validate over the core. Accept opaque vendor/session inputs, support two topic records per session and search title, project, vendor and ID fragment. Document root selection and exit behavior; test offline and with spaces.

Exercise the commands offline against a unique disposable registry under the
selected mounted Windows-profile test base, plus local controls. Verify the
explicit `AGENT_CONTEXT_HOME` and resolved-root display; clean up only test
artifacts and record the mounted-filesystem result separately.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[cli spec](../spec.md) and [execution protocol](../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
