---
id: 03-command-line
status: done
depends_on: [cli/02-core]
touches:
  - src/**
  - tests/test_cli*
  - pyproject.toml
  - README.md
lane: cli
gate: "manual: execute the step checks and record exact commands and results"
requirements: [R3, R4, R5]
evidence: "2026-11-07 WSL2, Python 3.12.3 / PyYAML 6.0.1: PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_cli*.py' -v passed 3 tests locally; the same command with AGENT_CONTEXT_TEST_PARENT set to a unique disposable child of the Windows-profile ai-dist-mem mount passed 3 tests outside the sandbox. These exercised every command, root display, opaque IDs, UTF-8, spaced paths, two topics, error exits, and 12 independent concurrent creates. Offline installation with pip --no-build-isolation --no-deps and PIP_NO_INDEX=1 into a temporary system-site-packages venv succeeded; installed register and validate passed. See results.md for procedures and limitations."
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
