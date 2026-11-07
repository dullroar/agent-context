# wsl-test — restartable execution prompt

Once the relevant work is authorized, use from the repository root:

```text
/goal Execute plans/wsl-test using plans/wsl-test/spec.md and plans/wsl-test/steps/.
Continue until verified complete or a plan-defined escalation requires a
decision. Report which outcome occurred and supporting evidence; do not report
an escalation or unavailable test as completion.
```

Read [the plan protocol](../README.md), [the spec](spec.md), repository
instructions and the step metadata first. Honor cross-plan dependencies and
file ownership; integrate independent lanes and run combined validation. Set
`status: done` only with evidence; resume from recorded state. Preserve the
working tree, do not commit or push without separate authorization, and do not
infer authority to alter personal or employer configuration.
