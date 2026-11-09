#!/usr/bin/env python3
"""Install isolated, reversible CLI launchers; never edit vendor settings."""
from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import uuid

AGENTS = ('codex', 'claude', 'copilot')
VERIFIED_WSL_VERSIONS = {
    'codex': 'codex-cli 0.157.0',
    'claude': '2.1.319 (Claude Code)',
    'copilot': 'GitHub Copilot CLI 1.0.107',
}
GUIDANCE = '''# Agent-context guidance

At the start of relevant work, search the local session registry for prior
sessions. Check that AGENT_CONTEXT_HOME identifies the intended registry
before searching or writing; when it is unset or uncertain, ask the operator
for the intended root rather than silently using a different registry. When
useful work is recorded, register a pointer or safely update one when a
supported mechanism exists, using an actually observed native session ID, an
environment-neutral project identity and a meaningful title. If an identifier
or update mechanism is unavailable, explain the manual fallback; do not invent
an identifier. Use unknown for an unobserved status.
Registry failures must not interrupt the user's work. Do not store prompts,
transcripts or secrets. A pointer does not establish resumability.

Example: agent-context search "topic"
For registration, run agent-context register --help and supply actual values.
These instructions are advisory; do not assume a search or registration
occurred without observing its result.
'''
BEGIN = b'<!-- BEGIN agent-context managed instructions -->'
END = b'<!-- END agent-context managed instructions -->'
BLOCK = b'\n\n' + BEGIN + b'\n' + GUIDANCE.encode('utf-8') + END + b'\n'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def managed_home() -> Path:
    override = os.environ.get('AGENT_CONTEXT_SETUP_HOME')
    if override:
        return Path(override).expanduser().absolute()
    if os.name == 'nt':
        return Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'agent-context' / 'integrations'
    return Path.home() / '.local' / 'share' / 'agent-context' / 'integrations'


def preflight(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    probe = root / ('.agent-context-setup-' + uuid.uuid4().hex)
    created = False
    try:
        with probe.open('xb') as stream:
            created = True
            stream.write(b'agent-context setup probe\n')
            stream.flush()
        if probe.read_bytes() != b'agent-context setup probe\n':
            raise OSError('probe contents differ')
        probe.unlink()
        created = False
    finally:
        if created:
            try:
                probe.unlink()
            except OSError:
                pass


def probe_agent(name: str) -> tuple[str, str]:
    executable = shutil.which(name)
    if not executable:
        return 'absent', 'executable not found'
    if (name == 'copilot' and os.name == 'nt' and
            'copilot-shim' in re.split(r'[\\/]+', executable.casefold())):
        return 'unsupported', 'VS Code Copilot shim has not been verified as a standalone CLI'
    if os.name != 'nt' and executable.lower().endswith(('.exe', '.cmd', '.bat')):
        return 'unsupported', 'Windows executable or shim on a non-Windows host'
    try:
        result = subprocess.run([executable, '--version'], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=8, check=False)
        help_result = subprocess.run([executable, '--help'], stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     timeout=8, check=False)
        expected = {'codex': b'codex', 'claude': b'claude', 'copilot': b'copilot'}[name]
        if (result.returncode or expected not in result.stdout.lower() or
                help_result.returncode or expected not in help_result.stdout.lower()):
            return 'failed', 'version or help probe did not identify a working CLI'
    except (OSError, subprocess.TimeoutExpired):
        return 'failed', 'version probe could not run or timed out'
    return 'available', str(Path(executable).absolute())


def psquote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def hook_supported(name: str, executable: str) -> bool:
    if not sys.platform.startswith('linux') or 'microsoft' not in os.uname().release.lower():
        return False
    try:
        result = subprocess.run([executable, '--version'], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    first = result.stdout.decode('utf-8', errors='replace').splitlines()
    return result.returncode == 0 and bool(first) and first[0].strip().rstrip('.') == VERIFIED_WSL_VERSIONS[name]


def artifacts(name: str, executable: str, root: Path, directory: Path | None = None,
              enable_hook: bool = False) -> dict[str, bytes]:
    extra = {}
    if enable_hook:
        if directory is None:
            raise ValueError('managed directory is required for hook artifacts')
        for filename in ('hook_context.py', 'hook_watch.py', 'launch_with_hook_watch.py'):
            extra[filename] = Path(__file__).with_name(filename).read_bytes()
        hook_command = shlex.join([sys.executable, str(directory / 'hook_context.py'), name])
        handler = {'type': 'command', 'command': hook_command, 'timeout': 4}
        if name == 'codex':
            argument = ('hooks.SessionStart=[{ hooks = [{ type = "command", command = ' +
                        json.dumps(hook_command, ensure_ascii=True) + ', timeout = 4 }] }]\n')
            extra['hook-argument.txt'] = argument.encode('utf-8')
        elif name == 'claude':
            config = {'hooks': {'SessionStart': [{'hooks': [handler]}]}}
            extra['hook-settings.json'] = (json.dumps(config, sort_keys=True) + '\n').encode('utf-8')
        else:
            config = {'version': 1, 'hooks': {'sessionStart': [{'type': 'command',
                      'bash': hook_command, 'timeoutSec': 4}]}}
            extra['hook-settings.json'] = (json.dumps(config, sort_keys=True) + '\n').encode('utf-8')
    if os.name == 'nt':
        wrapper = ("$env:AGENT_CONTEXT_HOME = " + psquote(str(root)) + "\n"
                   "[Console]::Error.WriteLine('agent-context: search prior sessions; record useful work with observed IDs.')\n"
                   "& " + psquote(executable) + " @args\nexit $LASTEXITCODE\n")
        filename = name + '.ps1'
    else:
        command = shlex.quote(executable)
        if enable_hook:
            launcher = [sys.executable, str(directory / 'launch_with_hook_watch.py'), '--provider', name]
            if name == 'codex':
                launcher += ['--config', str(directory / 'hook-argument.txt')]
            elif name == 'claude':
                launcher += ['--config', str(directory / 'hook-settings.json')]
            command = shlex.join([*launcher, '--', executable])
        wrapper = ('#!/bin/sh\nAGENT_CONTEXT_HOME=' + shlex.quote(str(root)) + '\n'
                   'export AGENT_CONTEXT_HOME\n'
                   "printf '%s\\n' 'agent-context: search prior sessions; record useful work with observed IDs.' >&2\n"
                   'exec ' + command + ' "$@"\n')
        filename = name
    wrapper_bytes = wrapper.encode('utf-8')
    if os.name == 'nt':
        wrapper_bytes = codecs.BOM_UTF8 + wrapper_bytes
    return {filename: wrapper_bytes, 'instructions.md': GUIDANCE.encode('utf-8'), **extra}


def instruction_path(name: str) -> Path:
    default_home = Path.home()
    if name == 'codex':
        directory = Path(os.environ.get('CODEX_HOME') or default_home / '.codex')
        override = directory / 'AGENTS.override.md'
        return override if override.exists() or override.is_symlink() else directory / 'AGENTS.md'
    if name == 'claude':
        return Path(os.environ.get('CLAUDE_CONFIG_DIR') or default_home / '.claude') / 'rules' / 'agent-context.md'
    return Path(os.environ.get('COPILOT_HOME') or default_home / '.copilot') / 'copilot-instructions.md'


def instruction_record(name: str, home: Path) -> Path:
    return home / name / 'instruction-owner.json'


def verify_instruction(name: str, home: Path) -> tuple[Path, dict | None]:
    record = instruction_record(name, home)
    path = instruction_path(name).absolute()
    if record.is_symlink():
        raise ValueError('instruction ownership record is a symlink')
    if not record.exists():
        return path, None
    state = json.loads(record.read_text(encoding='utf-8'))
    if (not isinstance(state, dict) or state.get('version') != 2 or
            state.get('path') != str(path) or state.get('sha256') != digest(BLOCK) or
            not isinstance(state.get('created'), bool)):
        raise ValueError('instruction ownership record does not match this environment')
    if path.is_symlink() or not path.is_file():
        raise ValueError('managed agent instructions missing or modified: ' + str(path))
    if not state['created'] or path.read_bytes() != BLOCK:
        raise ValueError('managed agent instructions missing or modified: ' + str(path))
    return path, state


def install_instruction(name: str, home: Path) -> str:
    path, state = verify_instruction(name, home)
    if state:
        return 'managed instructions present: ' + str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = instruction_record(name, home)
    if path.is_symlink():
        raise ValueError('instruction file is a symlink: ' + str(path))
    if path.exists():
        return 'manual: existing instructions preserved; add guidance after review: ' + str(path)
    created = False
    record_created = False
    try:
        with path.open('xb') as stream:
            created = True
            stream.write(BLOCK)
        with record.open('x', encoding='utf-8') as stream:
            record_created = True
            json.dump({'version': 2, 'path': str(path), 'sha256': digest(BLOCK), 'created': True}, stream, sort_keys=True)
            stream.write('\n')
    except Exception as exc:
        preserved_instruction = False
        if record_created:
            try:
                record.unlink()
            except OSError:
                pass
        if created:
            try:
                if not path.is_symlink() and path.read_bytes() == BLOCK:
                    path.unlink()
                else:
                    preserved_instruction = True
            except FileNotFoundError:
                pass
            except OSError:
                preserved_instruction = True
        if preserved_instruction:
            raise ValueError(f'{exc}; preserved instruction requiring inspection: {path}') from exc
        raise
    return 'installed managed instructions: ' + str(path)


def uninstall_instruction(name: str, home: Path) -> None:
    path, state = verify_instruction(name, home)
    if state:
        path.unlink()
        instruction_record(name, home).unlink()


def copilot_hook_path() -> Path:
    return (Path(os.environ.get('COPILOT_HOME') or Path.home() / '.copilot') /
            'hooks' / 'agent-context.json').absolute()


def verify_copilot_hook(home: Path) -> tuple[Path, bool]:
    record = home / 'copilot' / 'hook-owner.json'
    path = copilot_hook_path()
    if record.is_symlink():
        raise ValueError('hook ownership record is a symlink')
    if not record.exists():
        return path, False
    state = json.loads(record.read_text(encoding='utf-8'))
    artifact = home / 'copilot' / 'hook-settings.json'
    if (not isinstance(state, dict) or state.get('version') != 1 or
            state.get('path') != str(path) or not artifact.is_file() or
            state.get('sha256') != digest(artifact.read_bytes())):
        raise ValueError('hook ownership record does not match this environment')
    if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != state['sha256']:
        raise ValueError('managed Copilot hook missing or modified: ' + str(path))
    return path, True


def install_copilot_hook(home: Path) -> str:
    path, managed = verify_copilot_hook(home)
    if managed:
        return 'managed Copilot hook present: ' + str(path)
    if path.exists() or path.is_symlink():
        return ('manual: existing Copilot hook preserved: ' + str(path) +
                '; review managed hook settings: ' + str(home / 'copilot' / 'hook-settings.json'))
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (home / 'copilot' / 'hook-settings.json').read_bytes()
    record = home / 'copilot' / 'hook-owner.json'
    created = False
    record_created = False
    try:
        with path.open('xb') as stream:
            created = True
            stream.write(content)
        with record.open('x', encoding='utf-8') as stream:
            record_created = True
            json.dump({'version': 1, 'path': str(path), 'sha256': digest(content)}, stream, sort_keys=True)
            stream.write('\n')
    except Exception as exc:
        if record_created:
            try:
                record.unlink()
            except OSError:
                pass
        if created:
            try:
                if not path.is_symlink() and path.read_bytes() == content:
                    path.unlink()
                else:
                    raise ValueError(f'{exc}; preserved hook requiring inspection: {path}') from exc
            except FileNotFoundError:
                pass
        raise
    return 'installed Copilot hook: ' + str(path)


def uninstall_copilot_hook(home: Path) -> None:
    path, managed = verify_copilot_hook(home)
    if managed:
        path.unlink()
        (home / 'copilot' / 'hook-owner.json').unlink()


def load_manifest(directory: Path) -> dict:
    path = directory / 'manifest.json'
    if path.is_symlink():
        raise ValueError('managed manifest is a symlink')
    if not path.exists():
        return {}
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict) or result.get('version') != 1 or not isinstance(result.get('files'), dict):
        raise ValueError('invalid managed manifest')
    return result['files']


def safe_files(directory: Path, files: dict) -> None:
    for name, expected in files.items():
        if not isinstance(name, str) or Path(name).name != name or name in ('manifest.json', '.', '..'):
            raise ValueError('unsafe managed filename')
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError('invalid managed digest')
        path = directory / name
        if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError('managed file missing or modified: ' + name)


def install(name: str, executable: str, root: Path, home: Path, enable_hook: bool = False) -> Path:
    directory = home / name
    if directory.is_symlink():
        raise ValueError('managed directory is a symlink')
    directory.mkdir(parents=True, exist_ok=True)
    old = load_manifest(directory)
    safe_files(directory, old)
    new = artifacts(name, executable, root, directory, enable_hook)
    if set(old) - set(new):
        raise ValueError('unexpected managed files; inspect before retrying')
    for filename in new:
        path = directory / filename
        if filename not in old and (path.exists() or path.is_symlink()):
            raise ValueError('unmanaged file already exists: ' + filename)
    # Reserve each newly owned name exclusively. Existing owned names were
    # checked above. A failed install removes only files created by this run.
    created = []
    try:
        for filename, content in new.items():
            path = directory / filename
            if filename not in old:
                with path.open('xb') as stream:
                    created.append((path, content))
                    stream.write(content)
            elif path.read_bytes() != content:
                raise ValueError('managed content would change; uninstall first: ' + filename)
            if os.name != 'nt' and filename == name:
                path.chmod(0o700)
        manifest = directory / 'manifest.json'
        if not old:
            manifest_data = (json.dumps({'version': 1, 'files': {k: digest(v) for k, v in new.items()}}, sort_keys=True) + '\n').encode('utf-8')
            with manifest.open('xb') as stream:
                created.append((manifest, manifest_data))
                stream.write(manifest_data)
    except Exception as exc:
        preserved = []
        for path, content in reversed(created):
            try:
                if not path.is_symlink() and path.read_bytes() == content:
                    path.unlink()
                else:
                    preserved.append(str(path))
            except FileNotFoundError:
                pass
            except OSError:
                preserved.append(str(path))
        if preserved:
            raise ValueError(f'{exc}; preserved files requiring inspection: {", ".join(preserved)}') from exc
        raise
    return directory / (name + '.ps1' if os.name == 'nt' else name)


def uninstall(name: str, home: Path) -> str:
    directory = home / name
    manifest = directory / 'manifest.json'
    if not manifest.exists():
        return 'nothing managed'
    if directory.is_symlink() or manifest.is_symlink():
        raise ValueError('managed directory or manifest is a symlink')
    files = load_manifest(directory)
    safe_files(directory, files)
    for filename in files:
        (directory / filename).unlink()
    manifest.unlink()
    try:
        directory.rmdir()
    except OSError:
        pass
    return 'removed unchanged managed files'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', help='registry directory; omitted for an interactive prompt')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--inspect', action='store_true')
    modes.add_argument('--dry-run', action='store_true')
    modes.add_argument('--uninstall', action='store_true')
    args = parser.parse_args(argv)
    home = managed_home()
    print('Managed integration location:', home)
    if args.inspect or args.uninstall:
        failed = False
        for name in AGENTS:
            try:
                if args.uninstall:
                    directory = home / name
                    files = load_manifest(directory)
                    safe_files(directory, files)
                    verify_instruction(name, home)
                    if name == 'copilot':
                        verify_copilot_hook(home)
                        uninstall_copilot_hook(home)
                    uninstall_instruction(name, home)
                    result = uninstall(name, home)
                else:
                    directory = home / name
                    files = load_manifest(directory)
                    safe_files(directory, files)
                    _, instruction_managed = verify_instruction(name, home)
                    result = 'managed files verified' if files else 'not installed'
                    if instruction_managed:
                        result += '; managed instructions verified'
                    if name == 'copilot' and verify_copilot_hook(home)[1]:
                        result += '; managed Copilot hook verified'
                print(f'{name}: {result}')
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                print(f'{name}: failed: {exc}', file=sys.stderr)
                failed = True
        return int(failed)
    root_text = args.root
    if root_text is None:
        try:
            root_text = input('Where does the registry go? ').strip()
        except EOFError:
            root_text = ''
    if not root_text or '\x00' in root_text:
        print('setup: a registry location is required', file=sys.stderr)
        return 1
    root = Path(root_text).expanduser().absolute()
    print('Registry root:', root)
    if not args.dry_run:
        try:
            preflight(root)
        except OSError as exc:
            print(f'setup: root preflight failed: {exc}; no agent integrations changed', file=sys.stderr)
            return 1
    else:
        print('Dry run: root access was not tested and no files will be changed.')
    failures = False
    for name in AGENTS:
        status, detail = probe_agent(name)
        if status != 'available':
            print(f'{name}: {status}: {detail}')
            failures |= status == 'failed'
            continue
        enable_hook = hook_supported(name, detail)
        if args.dry_run:
            print(f'{name}: would install wrapper for {detail}; conflicts not checked')
            print(f'{name}: ' + ('would configure the tested WSL CLI hook' if enable_hook else
                                'hook unsupported or unverified for this host/version; manual fallback'))
            continue
        try:
            path = install(name, detail, root, home, enable_hook=enable_hook)
            print(f'{name}: installed CLI wrapper: {path}')
            print(f'{name}: {install_instruction(name, home)}')
            if enable_hook:
                if name == 'copilot':
                    print(f'{name}: {install_copilot_hook(home)}')
                else:
                    print(f'{name}: hook configured for this wrapper; existing agent settings are preserved')
                if name == 'codex':
                    print('codex: manual: review and trust the hook in /hooks; policy may disable it')
                print(f'{name}: hook verified only with a synthetic local provider; authentication and other interfaces unverified')
            else:
                print(f'{name}: hook unsupported or unverified for this host/version; manual fallback')
            print(f'{name}: manual: use that wrapper; review {path.parent / "instructions.md"}')
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f'{name}: failed: {exc}', file=sys.stderr)
            failures = True
    if not shutil.which('agent-context'):
        print('manual: install the agent-context CLI; wrapper operation does not require it')
    print('Inspect with --inspect; remove unchanged managed artifacts with --uninstall. Registry data is preserved.')
    return int(failures)


if __name__ == '__main__':
    if sys.version_info < (3, 10):
        print('setup: Python 3.10 or newer is required', file=sys.stderr)
        sys.exit(1)
    sys.exit(main())
