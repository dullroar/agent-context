# Setup integration results

Date: 2026-11-08. The setup integration gate covers offline and synthetic
checks. It does not establish authenticated vendor behavior or complete the
[WSL acceptance plan](../wsl-test/spec.md).

Later authenticated and cross-host observations are maintained separately in
[WSL acceptance results](../wsl-test/results.md); they do not change what this
offline integration gate itself established.

Environment: WSL2 Ubuntu, Python 3.12.3 / PyYAML 6.0.1; Windows PowerShell
5.1 and Windows Python 3.14.4. The chosen Windows-profile test base resolved
to `C:\Users\jimle\ai-dist-mem` and `/mnt/c/Users/jimle/ai-dist-mem` in this
run. Those are observations, not product defaults or project identity. Tests
used disposable children and isolated agent settings; no personal agent
configuration, external model service, or paid API was used.

## Offline suite

From the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Local WSL result: 75 discovered, 60 passed and 15 platform/opt-in checks skipped.
The same suite on the selected mounted base, including the cross-host reader
check, discovered 75, passed 61 and skipped 14 Windows-native/opt-in checks:

```bash
set -eu
agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')"
agent_context_win_profile="${agent_context_win_profile%$'\r'}"
test -n "$agent_context_win_profile"
agent_context_base="$(wslpath -u "$agent_context_win_profile")/ai-dist-mem"
test -d "$agent_context_base"
agent_context_test_dir="$(mktemp -d "$agent_context_base/setup-integration-XXXXXXXX")"
trap 'rmdir "$agent_context_test_dir"' EXIT
AGENT_CONTEXT_TEST_PARENT="$agent_context_test_dir" AGENT_CONTEXT_CROSS_TEST=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The cross-host check used an exclusive Windows writer and WSL readers. The
Windows-native tests below cover the corresponding native sharing behavior;
a skipped check is not counted as a pass in the run that skipped it.

Windows Python ran the full offline suite from disposable copies of `src`,
`tests`, `scripts` and the already-installed pure-Python PyYAML files; no
package was installed into Windows Python. Result: 75 discovered, 33 passed and
42 WSL/POSIX/opt-in checks skipped. The test copies and roots were removed.
The command used was:

```bash
set -eu
agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')"
agent_context_win_profile="${agent_context_win_profile%$'\r'}"
agent_context_base="$(wslpath -u "$agent_context_win_profile")/ai-dist-mem"
agent_context_test_dir="$(mktemp -d "$agent_context_base/setup-windows-XXXXXXXX")"
trap 'rm -rf "$agent_context_test_dir"' EXIT
cp -a src tests scripts "$agent_context_test_dir/"
mkdir "$agent_context_test_dir/src/yaml" "$agent_context_test_dir/test roots"
cp /usr/lib/python3/dist-packages/yaml/*.py "$agent_context_test_dir/src/yaml/"
cat > "$agent_context_test_dir/run_tests.py" <<'PY'
import os, pathlib, sys
base = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(base / 'src'))
os.environ['AGENT_CONTEXT_TEST_PARENT'] = str(base / 'test roots')
os.environ['TEMP'] = str(base / 'test roots')
os.environ['TMP'] = str(base / 'test roots')
import unittest
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(base / 'tests')))
raise SystemExit(not result.wasSuccessful())
PY
/mnt/c/Python314/python.exe "$(wslpath -w "$agent_context_test_dir/run_tests.py")"
```

The Windows path to Python in that command is specific to this test host. The
installer itself discovers Windows Python and does not hardcode it.

## Installed WSL CLI integration with synthetic providers

The actual installed Codex 0.157.0, Claude Code 2.1.319, and Copilot CLI
1.0.107 were run through setup-generated wrappers with isolated homes. The
following test was run both locally and with `AGENT_CONTEXT_TEST_PARENT` set to
a unique child of the selected shared base:

```bash
unshare -Urn bash -c 'ip link set lo up && AGENT_CONTEXT_INSTALLED_MOCK=1 PYTHONPATH=src python3 -m unittest discover -s tests -p "test_setup_installed_mock.py" -v'
```

Both runs passed. The test checks the private namespace has only loopback,
uses fake credentials and synthetic HTTP responses, and records no raw request
or hook payload. It verifies the installed start hook's guidance and observed
native session ID reached the fake provider, existing user hooks also ran,
and rerun and teardown preserved those settings. It forcibly terminates and
separately stalls each installed hook; the wrapper reports a bounded warning
while the synthetic turn completes. It also checks a missing root produces a
terminal warning and agent-visible warning context without blocking the turn.
For Codex and Claude the ID delivered by the hook was compared to the ID in
the corresponding synthetic CLI session output. Copilot ID presence was
observed but not independently compared in that test.

Separate opt-in provider suites exercised raw event JSON and exit-2 behavior.
A raw hook timeout or forced termination produced no captured provider warning
in the tested noninteractive modes; the installed per-launch monitor provides
the tested terminal warning for marked hooks. The monitor reports an
unconfirmed start when no hook completes, but cannot report after the whole
launcher is killed. Root access probes are advisory and do not guarantee a
subsequent write. See the [scripts step](steps/02-scripts.md) for the initial
failed Copilot shared-root run, its cleanup, and the corrected retry.

A separate `AGENT_CONTEXT_SETUP_REAL_AGENTS=1` run used only `--version` and
`--help`, with isolated homes and no personal credentials, to observe the
selected root in each real WSL agent process. It passed locally and on the
shared mount. Windows Claude Code 2.1.317 ran `--version` through its generated
PowerShell wrapper in an isolated profile. The actual Windows VS Code Copilot
shim was identified without executing it and reported unsupported pending
verification. The reusable procedure is in
[`tests/test_setup_windows_real.ps1`](../../tests/test_setup_windows_real.ps1).
These version checks do not establish authenticated sessions.

## Requirement reconciliation

| Requirement | Result and evidence | Limits |
| --- | --- | --- |
| R1 | Bash and PowerShell support root selection, inspection, dry-run, rerun and teardown; tests cover existing files, modified managed files, and safe failure. The [guide](../../docs/setup.md) documents install, update, uninstall and troubleshooting. | Existing instruction files are left intact and require manual merge; an updated managed artifact requires teardown before reinstall. |
| R2 | The [adoption design](adoption.md), guide, instruction snippets and optional skill distinguish hooks, guidance and procedure. | Instructions and skills are advisory. Copilot skill discovery was observed; automatic invocation or compliance was not. |
| R3 | WSL CLI start events and opaque IDs were observed against local fake providers; unsupported versions and Windows hooks are reported. | No authenticated vendor resume, real session status, IDE, desktop or cloud behavior is claimed. |
| R4 | Unit and installed integration checks exercise missing roots, worker failures, exit code 2, interruption, timeout, warning/status and continued synthetic turns. | The monitor cannot report after the entire launcher is killed; arbitrary filesystem I/O cannot be guaranteed nonblocking. |
| R5 | Offline tests cover configuration merging through per-launch settings, repeated setup, no-clobber, teardown, quoting/spaces, missing CLI, simulated failures and hook events. Copy-paste examples and the interface matrix are in the guide. | Authenticated and cross-interface acceptance belongs to the WSL plan and is not inferred from the mock provider. |
| R6 | Both actual shell entry points were exercised, including the single prompt, argument, preflight, failed preflight before agent mutation and cleanup. | A simulated denied probe is not evidence about every filesystem's ACL behavior. |
| R7 | Detection combinations and partial failures were tested with isolated fakes on both OSes; actual WSL CLIs and the Windows Claude launcher were checked separately. | A CLI or shim on PATH does not prove authentication or another interface's support. Windows hook integrations and the VS Code Copilot shim remain unverified. |

The guide's shared-root probe passed WSL write/read and Windows read, then its
unique child was removed. Its Bash and PowerShell examples parsed, and its
isolated dry-run examples did not create a registry or agent integration.
The optional skill passed the skill-creator validator and was discovered in an
isolated Copilot project; discovery is not proof of invocation.
