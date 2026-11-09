import os
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = ROOT / 'scripts' / 'launch_with_hook_watch.py'
WATCH = ROOT / 'scripts' / 'hook_watch.py'
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    SPEC = importlib.util.spec_from_file_location('agent_context_hook_launcher', LAUNCH)
    launcher = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(launcher)
finally:
    sys.path.pop(0)


@unittest.skipUnless(sys.platform.startswith('linux'), 'watch launcher is only implemented on Linux')
class HookLauncherTests(unittest.TestCase):
    def test_interrupted_hook_warns_while_agent_work_finishes(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            fake_agent = Path(directory) / 'agent.py'
            fake_agent.write_text('''import os,subprocess,sys,time
code = "import importlib.util,os,signal,sys;s=importlib.util.spec_from_file_location('w',sys.argv[1]);w=importlib.util.module_from_spec(s);s.loader.exec_module(w);w.mark_start(os.environ['AGENT_CONTEXT_HOOK_STATUS_DIR']);os.kill(os.getpid(),signal.SIGKILL)"
subprocess.run([sys.executable,'-c',code,sys.argv[1]])
time.sleep(0.4)
print('normal agent work completed')
''', encoding='utf-8')
            result = subprocess.run([sys.executable, str(LAUNCH), '--', sys.executable, str(fake_agent), str(WATCH)],
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('normal agent work completed', result.stdout)
            self.assertIn('hook was interrupted or did not finish', result.stderr)

    def test_arguments_and_agent_exit_code_are_preserved(self):
        code = 'import sys; print(sys.argv[1]); sys.exit(7)'
        result = subprocess.run([sys.executable, str(LAUNCH), '--', sys.executable, '-c', code, 'argument with spaces'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 7)
        self.assertIn('argument with spaces', result.stdout)
        self.assertIn('no completed hook event was observed', result.stderr)

    def test_explicit_agent_config_is_preserved(self):
        warnings = []
        codex = ['codex', 'exec', '-c', 'hooks.SessionStart=[]', 'task']
        claude = ['claude', '--settings', 'user settings.json', 'task']
        self.assertEqual(launcher.add_hook_config('codex', 'unused', codex, warnings.append), codex)
        self.assertEqual(launcher.add_hook_config('claude', 'unused', claude, warnings.append), claude)
        self.assertEqual(len(warnings), 2)
        self.assertTrue(all('preserved' in warning for warning in warnings))

    def test_per_launch_config_is_added_without_shell_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "settings ' with spaces"
            config.write_text('hooks.SessionStart=[]', encoding='utf-8')
            codex = launcher.add_hook_config('codex', str(config), ['codex', 'exec', 'argument with spaces'])
            claude = launcher.add_hook_config('claude', str(config), ['claude', 'argument with spaces'])
            self.assertEqual(codex, ['codex', '-c', 'hooks.SessionStart=[]', 'exec', 'argument with spaces'])
            self.assertEqual(claude, ['claude', '--settings', str(config), 'argument with spaces'])

    def test_monitor_setup_failure_does_not_block_agent(self):
        warnings = []
        with mock.patch.object(launcher.tempfile, 'TemporaryDirectory', side_effect=OSError('denied')):
            code = launcher.launch([sys.executable, '-c', 'import sys;sys.exit(7)'], reporter=warnings.append)
        self.assertEqual(code, 7)
        self.assertTrue(any('monitor unavailable' in warning for warning in warnings))

    def test_missing_hook_is_reported_while_agent_keeps_running(self):
        warnings = []
        code = launcher.launch([sys.executable, '-c', 'import time;time.sleep(0.3)'],
                               reporter=warnings.append, interval=0.02, startup_grace=0.05)
        self.assertEqual(code, 0)
        self.assertTrue(any('has not been confirmed' in warning for warning in warnings))

    def test_monitor_failure_does_not_change_agent_exit(self):
        warnings = []
        with mock.patch.object(launcher.HookMonitor, 'scan', side_effect=OSError('failed')):
            code = launcher.launch([sys.executable, '-c', 'import sys;sys.exit(7)'], reporter=warnings.append)
        self.assertEqual(code, 7)
        self.assertTrue(any('monitor failed' in warning for warning in warnings))

    def test_monitor_cleanup_failure_does_not_change_agent_exit(self):
        warnings = []
        with tempfile.TemporaryDirectory() as directory:
            temporary = mock.Mock(name=directory)
            temporary.name = directory
            temporary.cleanup.side_effect = OSError('failed')
            with mock.patch.object(launcher.tempfile, 'TemporaryDirectory', return_value=temporary):
                code = launcher.launch([sys.executable, '-c', 'import sys;sys.exit(7)'], reporter=warnings.append)
        self.assertEqual(code, 7)
        self.assertTrue(any('monitor cleanup failed' in warning for warning in warnings))


if __name__ == '__main__':
    unittest.main()
