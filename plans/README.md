# Plans and execution protocol

Four proposed plans preserve the v0 session-pointer boundary. Their `spec.md`
files state outcomes and protected checks; numbered steps record work and
verification. Each `goal.md` gives a restartable execution prompt. Proposal
status is not a claim that implementation or integration has been tested.

| Plan | Purpose | Main dependency |
| --- | --- | --- |
| [research](research/spec.md) | Establish vendor and storage facts, then update RESEARCH.md | None |
| [cli](cli/spec.md) | Implement the original foundation CLI | Research decisions before affected implementation |
| [setup](setup/spec.md) | Scripts, hooks, instructions and human setup | Research findings and CLI contract |
| [wsl-test](wsl-test/spec.md) | Exercise WSL, VS Code, Claude and Codex | CLI and setup ready |

## Dependencies and parallel work

Step `depends_on` entries use `plan/step-id`, including across plans. A step
starts only when its listed prerequisites are done with evidence. Within and
across plans, steps may run concurrently only if neither depends on the other
and their `touches` do not overlap; otherwise serialize. Each step also owns
its own step file for status and evidence, even when it is not listed in
`touches`. Research steps write
the same RESEARCH.md and therefore run serially. Read each step's full text as
well as its metadata: downstream steps can begin as soon as their precise
prerequisites are complete, not necessarily when an entire plan is complete.
Use isolated branches or worktrees if practical, integrate each lane, and run
the applicable combined validation after integration. Shared documentation,
specification decisions, and final integration have a single owner at a time.

The four specs are proposed work, not blanket approval for live paid API calls,
changes to workplace systems or policy, installing extensions, or modifying
personal configuration. Research and local, reversible offline work may proceed
within the task's authorization; seek the relevant authority for the rest.
Do not commit or push unless separately requested. Preserve existing changes.
For each step record command or manual procedure, environment, date, outcome,
and limitations in `evidence`; do not mark a skipped or unavailable check as
passed. A blocked external environment is reported as such, with the remaining
checks visible. Never silently weaken an acceptance check.
