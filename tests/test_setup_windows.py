import os
import ctypes
import importlib.util
import io
import itertools
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('agent_context_setup_windows', ROOT / 'scripts' / 'setup.py')
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


@unittest.skipUnless(os.name == 'nt', 'requires Windows PowerShell and Windows Python')
class WindowsSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT'))
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / 'fake bin'
        self.bin.mkdir()
        self.home = self.base / 'config home'
        self.root = self.base / "registry's space café"
        self.capture = self.base / 'capture.txt'
        self.env = os.environ.copy()
        self.env['AGENT_CONTEXT_SETUP_HOME'] = str(self.home)
        self.env['CODEX_HOME'] = str(self.base / 'codex profile')
        self.env['CLAUDE_CONFIG_DIR'] = str(self.base / 'claude profile')
        self.env['COPILOT_HOME'] = str(self.base / 'copilot profile')
        self.env['SETUP_CAPTURE'] = str(self.capture)
        buffer = ctypes.create_unicode_buffer(32768)
        if not ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer)):
            raise OSError('GetSystemDirectoryW failed')
        system_root = Path(buffer.value).parent
        self.env['SystemRoot'] = str(system_root)
        self.powershell = system_root / 'System32' / 'WindowsPowerShell' / 'v1.0' / 'powershell.exe'
        python_dir = str(Path(os.sys.executable).parent)
        self.env['PATH'] = os.pathsep.join([str(self.bin), python_dir, str(system_root / 'System32'), str(system_root)])

    def fake(self, name, broken=False):
        body = '@echo off\r\n'
        if broken:
            body += 'exit /b 4\r\n'
        else:
            body += ('if "%~1"=="--version" (echo ' + name + ' 1& exit /b 0)\r\n'
                     'if "%~1"=="--help" (echo ' + name + ' help& exit /b 0)\r\n'
                     'python -c "import os,sys,pathlib;pathlib.Path(os.environ[\'SETUP_CAPTURE\']).write_text(os.environ[\'AGENT_CONTEXT_HOME\']+chr(10)+sys.argv[1],encoding=\'utf-8\')" "%~1"\r\n'
                     'exit /b 7\r\n')
        (self.bin / (name + '.cmd')).write_text(body, encoding='ascii')

    def run_setup(self, *args, input=None):
        return subprocess.run([str(self.powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                               '-File', str(ROOT / 'scripts' / 'setup.ps1'), *map(str, args)],
                              input=input, capture_output=True, text=True, env=self.env)

    def test_powershell_install_forwarding_and_safe_teardown(self):
        for name in ('codex', 'claude', 'copilot'):
            self.fake(name)
        result = self.run_setup(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ('codex', 'claude', 'copilot'):
            self.assertIn(name + ': installed CLI wrapper', result.stdout)
            wrapper = self.home / name / (name + '.ps1')
            child = subprocess.run([str(self.powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                                    '-File', str(wrapper), 'argument with spaces'], env=self.env, capture_output=True, text=True)
            self.assertEqual(child.returncode, 7, child.stdout + child.stderr)
            self.assertEqual(self.capture.read_text(encoding='utf-8').splitlines(), [str(self.root), 'argument with spaces'])
        self.assertEqual(self.run_setup(self.root).returncode, 0)
        self.assertEqual(self.run_setup('--inspect').returncode, 0)
        self.assertEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertTrue(self.root.is_dir())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_preflight_precedes_install_and_broken_shim_is_reported(self):
        self.fake('codex', broken=True)
        self.fake('claude')
        self.root.write_text('unrelated')
        failed = self.run_setup(self.root)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn('no agent integrations changed', failed.stderr)
        self.assertFalse(self.home.exists())
        self.root.unlink()
        result = self.run_setup(self.root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('codex: failed:', result.stdout)
        self.assertIn('claude: installed CLI wrapper', result.stdout)
        self.assertIn('copilot: absent:', result.stdout)

    def test_denied_probe_leaves_agent_configuration_untouched(self):
        self.fake('codex')
        original_open = Path.open
        def deny_probe(path, *args, **kwargs):
            if path.name.startswith('.agent-context-setup-'):
                raise PermissionError('synthetic denied write')
            return original_open(path, *args, **kwargs)
        errors = io.StringIO()
        with mock.patch.dict(os.environ, self.env, clear=True):
            with mock.patch.object(Path, 'open', autospec=True, side_effect=deny_probe):
                with redirect_stdout(io.StringIO()), redirect_stderr(errors):
                    result = setup.main([str(self.root)])
        self.assertNotEqual(result, 0)
        self.assertIn('no agent integrations changed', errors.getvalue())
        self.assertFalse(self.home.exists())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_presence_combinations_no_clobber_and_retry(self):
        names = ('codex', 'claude', 'copilot')
        for combination in itertools.product((False, True), repeat=3):
            with self.subTest(combination=combination):
                for name, enabled in zip(names, combination):
                    path = self.bin / (name + '.cmd')
                    if path.exists():
                        path.unlink()
                    if enabled:
                        self.fake(name)
                result = self.run_setup(self.root)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                for name, enabled in zip(names, combination):
                    self.assertIn(name + (': installed CLI wrapper' if enabled else ': absent:'), result.stdout)
                self.assertEqual(self.run_setup('--uninstall').returncode, 0)
        self.fake('codex')
        self.assertEqual(self.run_setup(self.root).returncode, 0)
        wrapper = self.home / 'codex' / 'codex.ps1'
        wrapper.write_text('user edit')
        self.assertNotEqual(self.run_setup(self.root).returncode, 0)
        self.assertNotEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertEqual(wrapper.read_text(), 'user edit')

    def test_one_question_and_dry_run(self):
        self.fake('claude')
        result = self.run_setup('--dry-run', self.root)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.root.exists())
        self.assertFalse(self.home.exists())
        result = self.run_setup(input=str(self.root) + '\n')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count('Where does the registry go?'), 1)

    def test_existing_windows_instructions_are_left_unchanged(self):
        self.fake('codex')
        profile = Path(self.env['CODEX_HOME'])
        profile.mkdir()
        instructions = profile / 'AGENTS.md'
        instructions.write_text('existing user content')
        result = self.run_setup(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('existing instructions preserved', result.stdout)
        self.assertEqual(instructions.read_text(), 'existing user content')
        self.assertEqual(self.run_setup('--uninstall').returncode, 0)
        self.assertEqual(instructions.read_text(), 'existing user content')

    def test_vscode_copilot_shim_is_not_reported_as_installed(self):
        self.fake('copilot')
        shim_dir = self.base / 'copilot-shim'
        shim_dir.mkdir()
        (self.bin / 'copilot.cmd').replace(shim_dir / 'copilot.cmd')
        self.env['PATH'] = str(shim_dir) + os.pathsep + self.env['PATH']
        result = self.run_setup(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('copilot: unsupported: VS Code Copilot shim', result.stdout)
        self.assertFalse((self.home / 'copilot').exists())


if __name__ == '__main__':
    unittest.main()
