---
id: 04-interoperability
status: pending
depends_on: [research/03-shared-storage]
touches:
  - RESEARCH.md
lane: research
gate: "manual: compare RESEARCH.md and cited sources to step completion criteria"
requirements: [R4, R5]
evidence: ""
---

# Review existing implementations and interoperable standards

## Change

Review the three implementation references already linked in RESEARCH.md and the listed standards; record current licenses, maintenance, relevant design ideas and gaps, with primary sources and dates. Map proposed optional fields to OpenTelemetry, A2A and portable-memory work only where the semantics genuinely align. Update RESEARCH.md and recommend optional interoperability or upstream contribution only when evidence supports it.

## Dependencies and boundaries

Complete the cross-plan and local prerequisites in `depends_on` first. Follow
[research spec](../spec.md) and [execution protocol](../../README.md). Only touch
the files listed above; serialize any overlapping work. Do not weaken protected
checks or change unrelated files. Coordinate spec and shared documentation edits
with their owner.

## Completion and record

The change and the relevant requirement checks are complete, or a specific
blocking decision is escalated. Record source links or exact command/manual
procedure, environment, date, result and limitations in `evidence`; set
`status: done` only when the checks actually pass. Do not mark unavailable or
skipped verification as passed.
