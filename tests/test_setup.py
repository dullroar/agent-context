import importlib.util
import itertools
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('agent_context_setup', ROOT / 'scripts' / 'setup.py')
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


@unittest.skipIf(os.name == 'nt', 'Bash installer controls run on POSIX; Windows has separate PowerShell checks')
class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT'))
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / 'fake bin'
        self.bin.mkdir()
        self.home = self.base / 'config home'
        self.root = self.base / "registry's space $root"
        self.env = os.environ.copy()
        self.env['AGENT_CONTEXT_SETUP_HOME'] = str(self.home)
        self.env['CODEX_HOME'] = str(self.base / 'codex profile')
        self.env['CLAUDE_CONFIG_DIR'] = str(self.base / 'claude profile')
        self.env['COPILOT_HOME'] = str(self.base / 'copilot profile')
        self.env['PATH'] = str(self.bin) + os.pathsep + '/usr/bin:/bin'
        self.env['SETUP_CAPTURE'] = str(self.base / 'capture')

    def fake(self, name, broken=False):
        path = self.bin / name
        if broken:
            path.write_text('#!/bin/sh\nexit 4\n', encoding='utf-8')
        else:
            path.write_text('''#!/bin/sh
if [ "$1" = "--version" ] || [ "$1" = "--help" ]; then basename "$0"; exit 0; fi
printf '%s\\n' "$AGENT_CONTEXT_HOME" "$@" > "$SETUP_CAPTURE"
exit 7
''', encoding='utf-8')
        path.chmod(0o700)

    def run_setup(self, *args, input=None):
        return subprocess.run([str(ROOT / 'scripts' / 'setup.sh'), *map(str, args)],
                              input=input, text=True, capture_output=True, env=self.env)

    def test_detection_combinations_and_wrapper_forwarding(self):
        names = ('codex', 'claude', 'copilot')
        for combination in itertools.product((False, True), repeat=3):
            with self.subTest(combination=combination):
                for name, enabled in zip(names, combination):
                    path = self.bin / name
                    if path.exists():
                        path.unlink()
                    if enabled:
                        self.fake(name)
                result = self.run_setup(self.root)
                self.assertEqual(result.returncode, 0, result.stderr)
                for name, enabled in zip(names, combination):
                    self.assertIn(f'{name}: ' + ('installed CLI wrapper' if enabled else 'absent:'), result.stdout)
                    if enabled:
                        wrapper = self.home / name / name
                        child = subprocess.run([str(wrapper), 'argument with spaces', '$literal'], env=self.env, capture_output=True, text=True)
                        self.assertEqual(child.returncode, 7)
                        self.assertEqual((self.base / 'capture').read_text().splitlines(), [str(self.root), 'argument with spaces', '$literal'])
                self.assertEqual(self.run_setup('--uninstall').returncode, 0)

    def test_supported_hook_installation_for_all_detection_combinations(self):
        names = ('codex', 'claude', 'copilot')
        with mock.patch.dict(os.environ, self.env, clear=True):
            with mock.patch.object(setup, 'hook_supported', return_value=True):
                for combination in itertools.product((False, True), repeat=3):
                    with self.subTest(combination=combination):
                        for name, enabled in zip(names, combination):
                            path = self.bin / name
                            if path.exists():
                                path.unlink()
                            if enabled:
                                self.fake(name)
                        output, errors = io.StringIO(), io.StringIO()
                        with redirect_stdout(output), redirect_stderr(errors):
                            result = setup.main([str(self.root)])
                        self.assertEqual(result, 0, errors.getvalue())
                        for name, enabled in zip(names, combination):
                            self.assertEqual((self.home / name / 'hook_context.py').exists(), enabled)
                            self.assertIn(name + (': installed CLI wrapper' if enabled else ': absent:'), output.getvalue())
                        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                            self.assertEqual(setup.main(['--uninstall']), 0)

    def test_one_question_rerun_inspect_and_uninstall(self):
        self.fake('codex')
        first = self.run_setup(input=str(self.root) + '\n')
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout.count('Where does the registry go?'), 1)
        self.assertEqual(self.run_setup(self.root).returncode, 0)
        self.assertIn('codex: managed files verified', self.run_setup('--inspect').stdout)
        self.assertEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertTrue(self.root.is_dir())
        self.assertFalse((self.home / 'codex' / 'codex').exists())

    def test_root_failure_has_no_agent_mutation(self):
        self.fake('codex')
        self.root.write_text('unrelated', encoding='utf-8')
        result = self.run_setup(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no agent integrations changed', result.stderr)
        self.assertFalse(self.home.exists())
        self.assertEqual(self.root.read_text(), 'unrelated')

    def test_probe_failure_removes_own_probe(self):
        with mock.patch.object(Path, 'read_bytes', side_effect=OSError('simulated read failure')):
            with self.assertRaises(OSError):
                setup.preflight(self.root)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_agent_probe_timeout_and_plausible_but_broken_shim(self):
        with mock.patch.object(setup.shutil, 'which', return_value='/tmp/codex'):
            with mock.patch.object(setup.subprocess, 'run', side_effect=subprocess.TimeoutExpired('codex', 8)):
                self.assertEqual(setup.probe_agent('codex')[0], 'failed')
        shim = self.bin / 'codex'
        shim.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then echo codex; else exit 1; fi\n')
        shim.chmod(0o700)
        result = self.run_setup(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('codex: failed:', result.stdout)

    def test_nonfunctional_shim_and_partial_failure(self):
        self.fake('codex', broken=True)
        self.fake('claude')
        self.fake('copilot')
        directory = self.home / 'claude'
        directory.mkdir(parents=True)
        (directory / 'claude').write_text('user file', encoding='utf-8')
        result = self.run_setup(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('codex: failed:', result.stdout)
        self.assertIn('claude: failed:', result.stderr)
        self.assertIn('copilot: installed', result.stdout)
        self.assertEqual((directory / 'claude').read_text(), 'user file')
        (directory / 'claude').unlink()
        self.fake('codex')
        self.assertEqual(self.run_setup(self.root).returncode, 0)

    def test_modified_file_is_not_overwritten_or_deleted(self):
        self.fake('codex')
        self.assertEqual(self.run_setup(self.root).returncode, 0)
        wrapper = self.home / 'codex' / 'codex'
        wrapper.write_text('custom user edit', encoding='utf-8')
        self.assertNotEqual(self.run_setup(self.root).returncode, 0)
        self.assertNotEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertEqual(wrapper.read_text(), 'custom user edit')

    def test_existing_agent_instructions_are_preserved(self):
        self.fake('codex')
        profile = Path(self.env['CODEX_HOME'])
        profile.mkdir()
        existing = profile / 'AGENTS.md'
        existing.write_text('existing guidance\n', encoding='utf-8')
        result = self.run_setup(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('existing instructions preserved', result.stdout)
        self.assertEqual(existing.read_text(), 'existing guidance\n')
        with existing.open('a', encoding='utf-8') as stream:
            stream.write('later user guidance\n')
        self.assertEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertEqual(existing.read_text(), 'existing guidance\nlater user guidance\n')

    def test_existing_instruction_file_is_not_replaced(self):
        profile = self.base / 'codex profile'
        profile.mkdir()
        existing = profile / 'AGENTS.md'
        existing.write_text('original guidance\n', encoding='utf-8')
        existing.chmod(0o600)
        original_mode = existing.stat().st_mode & 0o777
        (self.home / 'codex').mkdir(parents=True)
        with mock.patch.dict(os.environ, self.env, clear=True):
            with mock.patch.object(setup.os, 'replace', side_effect=AssertionError('must not replace')):
                message = setup.install_instruction('codex', self.home)
        self.assertIn('existing instructions preserved', message)
        self.assertEqual(existing.read_text(encoding='utf-8'), 'original guidance\n')
        self.assertEqual(existing.stat().st_mode & 0o777, original_mode)
        self.assertFalse((self.home / 'codex' / 'instruction-owner.json').exists())

    def test_failed_instruction_install_preserves_a_new_file_edited_during_setup(self):
        (self.home / 'codex').mkdir(parents=True)
        instruction = Path(self.env['CODEX_HOME']) / 'AGENTS.md'

        def edit_then_fail(*args, **kwargs):
            instruction.write_text('user edited while setup was running', encoding='utf-8')
            raise OSError('simulated ownership-record failure')

        with mock.patch.dict(os.environ, self.env, clear=True):
            with mock.patch.object(setup.json, 'dump', side_effect=edit_then_fail):
                with self.assertRaisesRegex(ValueError, 'ownership-record failure.*preserved instruction'):
                    setup.install_instruction('codex', self.home)
        self.assertEqual(instruction.read_text(encoding='utf-8'), 'user edited while setup was running')
        self.assertFalse((self.home / 'codex' / 'instruction-owner.json').exists())

    def test_failed_wrapper_install_preserves_file_edited_during_setup(self):
        wrapper = self.home / 'codex' / 'codex'

        def edit_then_fail(path, mode):
            path.write_text('user edited while setup was running', encoding='utf-8')
            raise OSError('simulated chmod failure')

        with mock.patch.object(Path, 'chmod', autospec=True, side_effect=edit_then_fail):
            with self.assertRaisesRegex(ValueError, 'chmod failure.*preserved files'):
                setup.install('codex', '/usr/bin/codex', self.root, self.home)
        self.assertEqual(wrapper.read_text(encoding='utf-8'), 'user edited while setup was running')

    def test_modified_managed_agent_instructions_survive_retry_and_teardown(self):
        self.fake('claude')
        self.assertEqual(self.run_setup(self.root).returncode, 0)
        instruction = Path(self.env['CLAUDE_CONFIG_DIR']) / 'rules' / 'agent-context.md'
        self.assertTrue(instruction.exists())
        instruction.write_text('user changed instructions', encoding='utf-8')
        self.assertNotEqual(self.run_setup(self.root).returncode, 0)
        self.assertNotEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertEqual(instruction.read_text(), 'user changed instructions')

    def test_codex_override_is_preserved(self):
        self.fake('codex')
        profile = Path(self.env['CODEX_HOME'])
        profile.mkdir()
        (profile / 'AGENTS.override.md').write_text('existing override')
        result = self.run_setup(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        override = profile / 'AGENTS.override.md'
        self.assertIn('existing instructions preserved', result.stdout)
        self.assertEqual(override.read_text(), 'existing override')
        self.assertFalse((profile / 'AGENTS.md').exists())
        self.assertEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertEqual((profile / 'AGENTS.override.md').read_text(), 'existing override')

    def test_dry_run_does_not_create_root_or_integrations(self):
        self.fake('codex')
        result = self.run_setup('--dry-run', self.root)
        self.assertEqual(result.returncode, 0)
        self.assertIn('would install wrapper', result.stdout)
        self.assertFalse(self.root.exists())
        self.assertFalse(self.home.exists())

    def test_missing_registry_cli_does_not_block_wrapper(self):
        self.fake('claude')
        result = self.run_setup(self.root)
        self.assertEqual(result.returncode, 0)
        self.assertIn('install the agent-context CLI', result.stdout)
        child = subprocess.run([str(self.home / 'claude' / 'claude'), 'hello'], env=self.env)
        self.assertEqual(child.returncode, 7)

    def test_monitored_wrappers_forward_root_and_preserve_explicit_config(self):
        for name in ('codex', 'claude', 'copilot'):
            with self.subTest(agent=name):
                self.fake(name)
                executable = str(self.bin / name)
                wrapper = setup.install(name, executable, self.root, self.home, enable_hook=True)
                result = subprocess.run([str(wrapper), 'argument with spaces'], env=self.env,
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 7, result.stderr)
                args = (self.base / 'capture').read_text().splitlines()
                self.assertEqual(args[0], str(self.root))
                self.assertEqual(args[-1], 'argument with spaces')
                if name == 'codex':
                    self.assertEqual(args[1], '-c')
                    self.assertIn('hooks.SessionStart', args[2])
                elif name == 'claude':
                    self.assertEqual(args[1], '--settings')
                    self.assertTrue(Path(args[2]).is_file())
                else:
                    self.assertEqual(args[1:], ['argument with spaces'])
                if name in ('codex', 'claude'):
                    explicit = ['-c', 'user=value'] if name == 'codex' else ['--settings', 'user.json']
                    result = subprocess.run([str(wrapper), *explicit], env=self.env,
                                            capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 7, result.stderr)
                    self.assertEqual((self.base / 'capture').read_text().splitlines()[1:], explicit)
                    self.assertIn('preserved', result.stderr)
                self.assertIn('removed unchanged', setup.uninstall(name, self.home))

    def test_copilot_hook_file_is_independent_and_reversible(self):
        self.fake('copilot')
        with mock.patch.dict(os.environ, self.env, clear=True):
            setup.install('copilot', str(self.bin / 'copilot'), self.root, self.home, enable_hook=True)
            hooks = Path(self.env['COPILOT_HOME']) / 'hooks'
            hooks.mkdir(parents=True)
            other = hooks / 'existing.json'
            other.write_text('{"user": true}', encoding='utf-8')
            self.assertIn('installed Copilot hook', setup.install_copilot_hook(self.home))
            self.assertIn('managed Copilot hook present', setup.install_copilot_hook(self.home))
            self.assertEqual(other.read_text(encoding='utf-8'), '{"user": true}')
            setup.uninstall_copilot_hook(self.home)
            self.assertTrue(other.exists())
            target = hooks / 'agent-context.json'
            target.write_text('{"user": "existing"}', encoding='utf-8')
            self.assertIn('existing Copilot hook preserved', setup.install_copilot_hook(self.home))
            setup.uninstall_copilot_hook(self.home)
            self.assertEqual(target.read_text(encoding='utf-8'), '{"user": "existing"}')

    def test_modified_copilot_hook_is_not_removed(self):
        self.fake('copilot')
        with mock.patch.dict(os.environ, self.env, clear=True):
            setup.install('copilot', str(self.bin / 'copilot'), self.root, self.home, enable_hook=True)
            setup.install_copilot_hook(self.home)
            target = Path(self.env['COPILOT_HOME']) / 'hooks' / 'agent-context.json'
            target.write_text('user change', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'modified'):
                setup.uninstall_copilot_hook(self.home)
            self.assertEqual(target.read_text(encoding='utf-8'), 'user change')

    def test_failed_copilot_hook_install_preserves_concurrent_user_edit(self):
        self.fake('copilot')
        with mock.patch.dict(os.environ, self.env, clear=True):
            setup.install('copilot', str(self.bin / 'copilot'), self.root, self.home, enable_hook=True)
            target = Path(self.env['COPILOT_HOME']) / 'hooks' / 'agent-context.json'
            def edit_then_fail(*args, **kwargs):
                target.write_text('user edit during setup', encoding='utf-8')
                raise OSError('simulated owner write failure')
            with mock.patch.object(setup.json, 'dump', side_effect=edit_then_fail):
                with self.assertRaisesRegex(ValueError, 'preserved hook'):
                    setup.install_copilot_hook(self.home)
            self.assertEqual(target.read_text(encoding='utf-8'), 'user edit during setup')
            self.assertFalse((self.home / 'copilot' / 'hook-owner.json').exists())


if __name__ == '__main__':
    unittest.main()
