# Interoperability research

Research date: 2026-11-06. This is a design inventory, not a claim that any
project below has adopted this repository's proposed record format.

## Conclusion

No single mature open standard was found that jointly covers local
cross-vendor coding-agent session discovery, portable long-term memory,
tamper-evident provenance, and lifecycle management. The ecosystem has useful
parts; this project should compose with them rather than recreate them.

| Concern | Closest existing work | Fit | Deliberate gap for this project |
| --- | --- | --- | --- |
| Tool/data connectivity | [MCP](https://modelcontextprotocol.io/specification/) | Strong for exposing tools, prompts, and resources | It does not prescribe shared memory semantics or a portable local session registry. |
| Agent-to-agent collaboration and task lifecycle | [A2A](https://a2a-protocol.org/v1.0.1/topics/life-of-a-task/) | Strong for remote task state, artifacts, and `contextId` | It does not provide a human-facing catalog of local vendor sessions or track artifact mutation. |
| Portable agent memory | [Open Memory Protocol Initiative](https://ai-disclosures.org/ompi) and the [W3C memory interoperability CG](https://www.w3.org/community/ai-agent-memory-interop/) | Directly aligned with vendor-neutral memory portability | Still emerging; memory portability is broader than session discovery. |
| Observability correlation | [OpenTelemetry GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai) | Useful names for agent, conversation, message, and trace correlations | Telemetry does not supply persistent human discovery records. |
| Tamper-evident provenance | [in-toto Attestation Framework](https://in-toto.io/docs/specs/) and [SLSA provenance](https://slsa.dev/spec/v1.2/build-provenance) | Mature models for signed software-supply-chain statements | Their build-artifact focus is not a reason to impose signatures on local session notes. |

## Design implications

1. **Adopt concepts, not a false umbrella.** Use opaque native IDs; make room
   for OpenTelemetry correlation IDs; map lifecycle states to A2A only when an
   adapter actually speaks A2A.
2. **Do not compete with portable-memory initiatives.** A later adapter may
   link a session record to an OMP/W3C-compatible memory object, but v0 stores
   neither a memory graph nor a transcript.
3. **Use Git before cryptography.** For a versioned registry, Git commits offer
   inexpensive provenance. Add in-toto/SLSA-style attestations only for a real
   verification boundary.
4. **Keep MCP optional.** An MCP server could expose `register`, `search`, and
   `inspect` after the file format and CLI have proved useful. It should remain
   an adapter, not a prerequisite.

## Open investigation: agent hooks

Before selecting adapter integrations, investigate pre- and post-hooks across
the coding agents in use. Record evidence and test results for each agent and
version; support should be marked unknown until verified. Cover:

- Which pre- and post-events are available, including session, prompt, and
  tool lifecycle events, and what session or project identifiers they expose.
- Whether hooks work when the agent runs in VS Code and in its desktop UI,
  including any differences from its CLI.
- Whether each integration works on Windows and in WSL, where the hook executes,
  and how it resolves paths and the registry root in each environment.
- How hooks are configured, what happens when they fail or are interrupted,
  and whether registry updates can remain failure-open without exposing prompts
  or transcripts.

Capture the findings as an agent/version-by-interface-and-environment matrix,
with documentation links, test dates, observed limitations, and untested cases.
Use the results to choose adapter approaches; do not infer session lifecycle
events from hooks that cannot observe them.

## Related implementations to inspect before coding adapters

- [agents-memory](https://github.com/lolaplex/agents-memory) — Markdown-first,
  cross-agent memory implementation with session discovery ideas.
- [agent-memory-vault](https://github.com/mcncarl/agent-memory-vault) — shared
  Claude/Codex memory with Git, SQLite, and audit-oriented controls.
- [projectmem](https://github.com/riponcm/projectmem) — local event sourcing
  and deterministic projections for coding-agent memory.

These are implementation references, not endorsed dependencies. Validate their
current license, maturity, and active behavior before adoption.
