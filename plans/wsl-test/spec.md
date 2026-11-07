# WSL test — specification

Status: proposed

## Outcome

Exercise the installed registry in WSL first with Claude and Codex, including
VS Code connected to WSL where available. Then test available Windows-native
agents against the same Windows-profile `ai-dist-mem` base, plus desktop,
Copilot and a VM/shared-root scenario where available. Keep tested results
distinct from research and inference.

## Requirements and protected checks

- **R1 — WSL CLI:** with a disposable registry beneath the selected
  Windows-profile `ai-dist-mem` WSL mount and a test project, run register,
  list, search, show and validate offline; exercise spaces/UTF-8, multiple topics,
  concurrent independent records and simulated write failure. Record versions,
  resolved root, commands, exit status and results.
- **R2 — Real interfaces:** independently test Claude and Codex CLI in WSL,
  then each available VS Code WSL session target. Verify a real native session
  reference and observed event(s) against the integration's documented contract;
  confirm lookup from a separate session and only claim resume if actually
  tested through the vendor's supported flow. Use synthetic content and no
  transcript copying. A missing account, extension or feature is untested.
- **R3 — Windows/WSL and VM:** exercise available Windows-native agents and WSL
  agents against the same selected `ai-dist-mem` base, including overlapping
  sessions and independent record writes. Verify actual cross-host visibility,
  identity, root selection and path hints; test interrupted writes, concurrent
  creation and long-but-valid paths in a disposable child root. Record each
  host, agent and result. Evaluate `\\tsclient\C\Users\<username>\ai-dist-mem`
  only when RDP drive redirection and policy permit; verify access from every
  execution host, including VM WSL if used. Compare an approved share/sync
  alternative and record visibility, failure modes and conflict handling.
- **R4 — Copilot/desktop:** when available test GitHub Copilot in VS Code and
  relevant CLI or desktop interfaces; record supported versus unsupported
  hooks, policy restrictions, manual fallback and versions. Test desktop agents
  where their actual execution environment and data permissions allow.
- **R5 — Honest result:** publish a matrix of pass/fail/blocked/not tested with
  evidence and failure-open observations, exact environment, root mapping and
  remaining risks. A skipped interface never counts as a pass; plan completion
  requires the requested mounted-root WSL Claude/Codex, available Windows-agent
  and available VS Code checks, or an explicit plan-defined escalation
  describing the unavailable capability.

## Authority and validation

Use disposable synthetic records. Do not change employer systems, enable
redirection, install software, use paid APIs or transfer work data without the
appropriate authority. Existing authenticated interactive agents may be used
only within the permissions of the execution environment; document when human
interaction is required. Preserve independent records on interruption and do
not assume atomic rename or collision safety on remote storage. Run the full
offline suite before and after integration, plus the actual environment checks
above. Record exact test procedures and results in `results.md` and per-step
metadata. Escalate missing access or a failed protected acceptance check with
specific evidence; do not report escalation as completed acceptance.

Use [the shared test location](../README.md#shared-windowswsl-test-location)
from the first baseline onward. For filesystem stress use a unique disposable
child; real WSL and Windows agents should use the same configured base with
clearly identified synthetic records. Confirm visibility rather than assuming
the two spellings identify the same location. Never remove unrelated records;
an inaccessible mount or unavailable Windows-agent check is blocked/untested,
not a pass. The VM's RDP redirection is a separate, later test.
