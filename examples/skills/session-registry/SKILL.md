---
name: session-registry
description: Find or record a portable pointer to an observed agent session when working with an agent-context registry. Do not use as a transcript store or assume a vendor session is resumable.
---

# Session registry

Confirm `AGENT_CONTEXT_HOME` is the intended root. Search with `agent-context
search <topic>` and report unavailable-record warnings; a zero exit alone does
not prove the search was complete.

When useful work merits a pointer, use an observed native session ID, meaningful
title, and environment-neutral project identity. Run `agent-context register
--help` for the current options. Use `unknown` for status that was not
observed. If an ID or safe update mechanism is unavailable, explain the manual
fallback; never invent identifiers or assume registration or resume occurred.

Registry failures must not stop the user's work. Do not record prompts,
transcripts, or secrets. This skill is advisory and only applies when discovered
and invoked by the current host.
