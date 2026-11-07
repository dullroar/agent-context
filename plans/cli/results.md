# CLI acceptance results

This records the initial R1–R5 CLI acceptance and the separately verified
[snapshot-read extension](steps/05-snapshot-reads.md). The planned
[session-launch extension](steps/05-session-launch.md) is not implemented or tested.

Date: 2026-11-07. Environment: WSL2 Linux 6.6.87.2-microsoft-standard-WSL2,
Python 3.12.3, PyYAML 6.0.1. The Windows-profile root resolved in this run to
`/mnt/c/Users/jimle/ai-dist-mem`, a WSL mount of a Windows-hosted filesystem.
The path is evidence of this run, not a product default or project identity.

## Full offline suite: local control

From the repository root, with the already-installed PyYAML dependency:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Result: 14 tests passed; `git diff --check` passed. The suite makes no network,
model, daemon or service calls. Core and CLI tests create unique local temporary
children, including paths containing spaces, and remove them.

## Full offline suite: selected mounted test base

The following was run outside the sandbox, which cannot use WSL interop or write
to the Windows mount. It fails if profile resolution or the selected base is
unavailable; it does not create or change that base. The test runner removes its
own temporary children, and the shell trap removes the run's empty parent.

```bash
set -eu
agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')"
agent_context_win_profile="${agent_context_win_profile%$'\r'}"
test -n "$agent_context_win_profile"
agent_context_base="$(wslpath -u "$agent_context_win_profile")/ai-dist-mem"
test -d "$agent_context_base"
agent_context_test_dir="$(mktemp -d "$agent_context_base/cli-integration-XXXXXXXX")"
trap 'rmdir "$agent_context_test_dir"' EXIT
AGENT_CONTEXT_TEST_PARENT="$agent_context_test_dir" PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Result: 14 tests passed, including CLI subprocesses and filesystem tests;
the disposable parent was removed. Earlier focused runs passed 9 core tests
and 3 CLI tests on the same mount; final integrated tests include the subsequent
core and CLI changes. A preliminary WSL-write/Windows-read probe and its exact
procedure are recorded in step 01.

## Installable command check

On the same WSL/Python environment, this command built and installed a copy of
the package without an index, using an already-installed PyYAML and build tools
from system site packages. It successfully registered and validated a record
through the installed `agent-context` executable. The temporary copy, venv and
registry were removed. This tests an offline installation with dependencies
already available; it does not test downloading or Windows Python installation.

```bash
set -eu
agent_context_install_test="$(mktemp -d /tmp/agent-context-install-XXXXXXXX)"
trap 'rm -rf "$agent_context_install_test"' EXIT
mkdir "$agent_context_install_test/source"
cp -a pyproject.toml src "$agent_context_install_test/source/"
python3 -m venv --system-site-packages "$agent_context_install_test/venv"
PIP_NO_INDEX=1 "$agent_context_install_test/venv/bin/python" -m pip install --no-build-isolation --no-deps "$agent_context_install_test/source"
AGENT_CONTEXT_HOME="$agent_context_install_test/registry with spaces" "$agent_context_install_test/venv/bin/agent-context" register --producer codex --vendor codex --session 'opaque:session' --project git:example/repo --title 'Installed CLI test'
AGENT_CONTEXT_HOME="$agent_context_install_test/registry with spaces" "$agent_context_install_test/venv/bin/agent-context" validate
```

## Requirement coverage

| Requirement | Evidence |
| --- | --- |
| R1 | Spec 0001 records Jim's Python choice, PyYAML, schema, lifecycle, filename rules, and test-root contract. Fixtures contain two valid and fifteen invalid records plus filename cases; `test_fixtures`, `test_metadata_rules`, and `test_filename_cases_and_generation` exercise them. |
| R2 | Core tests cover configured/default roots, generated IDs, UTF-8 parsing, filename derivation, collision retry, complete-before-publication, successful replacement and replacement failure. CLI tests check displayed resolved roots. |
| R3 | End-to-end tests exercise register, list, all four search fields, show, and validate; two records share an opaque native session while having distinct IDs. No shared index is created. |
| R4 | Invalid metadata and names, UTF-8 and spaced paths, portable identity/path hints, simulated write failures and preservation, 40 concurrent core creates, and 12 separate concurrent CLI processes are covered on both targets. |
| R5 | The complete suite and its environment are recorded above. The package has no runtime service or model dependency. |

## Limits

The mounted run uses WSL to operate on a Windows-hosted local filesystem. It is
not a test of RDP shares, cloud synchronization, network-filesystem atomicity,
Windows-native Python, Windows/WSL agent integrations, vendor resume, or
same-record concurrent updates. Windows/WSL multi-interface agent acceptance
and setup remain in their respective plans. New registrations require same-directory hard-link support; failure is reported
if it is unavailable. A crash may leave a hidden temporary file. The CLI makes
no claim that links, rename, or replace are atomic on untested network filesystems.

## Snapshot-reader extension: 2026-11-07

The reader copies registry metadata into a private in-memory byte snapshot and
closes the source before parsing; it does not request registry locks. The Windows
reader explicitly allows read/write/delete sharing. The Windows writer requests
POSIX-style replacement where supported, falling back to ordinary replacement
on older systems/filesystems. An active agent's single-writer ownership is a
protocol rule, not an enforced operating-system lock. Vendor-native session
files are not read or copied by this feature.

### Offline test runs

WSL2 Python 3.12.3 / PyYAML 6.0.1 local control:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
git diff --check
```

Result: 20 tests discovered, 17 passed, 3 platform-specific checks skipped;
the Windows and cross-host checks were exercised in the runs below. WSL `cat`
and `less` 590 both read a pointer while another process held an advisory
exclusive `flock`, within the test's five-second timeout.

The full suite was then run on the selected Windows-profile mount from WSL,
with the cross-host test enabled (outside the sandbox):

```bash
set -eu
agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')"
agent_context_win_profile="${agent_context_win_profile%$'\r'}"
test -n "$agent_context_win_profile"
agent_context_base="$(wslpath -u "$agent_context_win_profile")/ai-dist-mem"
test -d "$agent_context_base"
agent_context_test_dir="$(mktemp -d "$agent_context_base/cli-snapshot-wsl-XXXXXXXX")"
trap 'rmdir "$agent_context_test_dir"' EXIT
AGENT_CONTEXT_TEST_PARENT="$agent_context_test_dir" AGENT_CONTEXT_CROSS_TEST=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Result: 20 tests discovered, 18 passed, 2 Windows-native checks skipped; those
checks passed in the next run. The cross-host test held a synthetic record open
with exclusive Windows sharing, then ran WSL readers with timeouts. WSL `cat`
received permission denied. WSL `less` did not return the record; in an earlier
manual probe it returned exit zero despite the failed read. The CLI warned that
the record was unavailable and returned other records without a nonzero exit;
`validate` reported the unavailable count and `show` emitted no record.

Windows-native Python 3.14.4 was run with a temporary copy of the source, tests,
and the pure-Python files from the locally installed PyYAML 6.0.1. Nothing was
installed into Windows Python. The following command was run outside the
sandbox; all copies and test roots were removed with the disposable directory.

```bash
set -eu
agent_context_win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")')"
agent_context_win_profile="${agent_context_win_profile%$'\r'}"
test -n "$agent_context_win_profile"
agent_context_base="$(wslpath -u "$agent_context_win_profile")/ai-dist-mem"
test -d "$agent_context_base"
agent_context_test_dir="$(mktemp -d "$agent_context_base/cli-windows-reader-XXXXXXXX")"
trap 'rm -rf "$agent_context_test_dir"' EXIT
cp -a src tests "$agent_context_test_dir/"
mkdir "$agent_context_test_dir/src/yaml" "$agent_context_test_dir/test roots"
cp /usr/lib/python3/dist-packages/yaml/*.py "$agent_context_test_dir/src/yaml/"
cat > "$agent_context_test_dir/run_tests.py" <<'PY'
import os, pathlib, sys, unittest
base = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(base / 'src'))
os.environ['AGENT_CONTEXT_TEST_PARENT'] = str(base / 'test roots')
suite = unittest.defaultTestLoader.discover(str(base / 'tests'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
PY
/mnt/c/Python314/python.exe "$(wslpath -w "$agent_context_test_dir/run_tests.py")"
```

Result: 20 tests discovered, 17 passed, 3 WSL/POSIX-specific checks skipped;
those checks passed in the preceding WSL run. With a writer allowing sharing,
Windows `TYPE` and the CLI read the synthetic file. With a fully exclusive
writer, `TYPE` failed and the CLI reported unavailability. A separate process
using the registry's replacement operation successfully replaced a record while
the explicit-sharing reader was open, and the reader finished its old snapshot.
The first test using ordinary `os.replace` failed on this Windows filesystem even
with a sharing reader; that failure motivated the POSIX-style replacement.

### Limits and sources

An external writer can deny reads; copying with `cat`, `less`, `TYPE`, or Python
cannot bypass that denial. A zero CLI exit in an unavailable-record case means
no invalid record or other error was detected, **not** that the result was
complete. List/search warn and return accessible records, validate reports
unavailable counts, and show emits no record when uniqueness cannot be checked.
Scripts must inspect warnings and output for completeness. These tests do not
prove nonblocking I/O on arbitrary network filesystems or safety with an external
in-place writer; an in-place copy can observe incomplete content.

Platform references: [Windows CreateFileW sharing modes](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[Windows replacement flags](https://learn.microsoft.com/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information),
and [Linux flock semantics](https://man7.org/linux/man-pages/man2/flock.2.html).
