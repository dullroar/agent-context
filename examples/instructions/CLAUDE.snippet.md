## Session registry

At the start of relevant work, confirm `AGENT_CONTEXT_HOME` identifies the
intended registry and search for prior sessions. If the root is unset or
uncertain, ask the operator rather than silently using another registry.

When useful work should be recorded, register a pointer using an observed native
session ID, a meaningful title, and an environment-neutral project identity.
Use `unknown` for unobserved status. If the ID or a safe update mechanism is
unavailable, explain the manual fallback; do not invent an ID or claim resume.
Registry failure must not stop the user's work. Do not store prompts,
transcripts, or secrets in pointer records.
