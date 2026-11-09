import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

WATCH = Path(__file__).resolve().parents[1] / 'scripts' / 'hook_watch.py'
SPEC = importlib.util.spec_from_file_location('agent_context_hook_watch', WATCH)
watch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watch)


@unittest.skipUnless(os.name == 'posix', 'process liveness behavior has only been tested on POSIX')
class HookWatchTests(unittest.TestCase):
    def test_normal_completion_has_no_interruption_warning(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            warnings = []
            token = watch.mark_start(directory)
            watch.mark_done(directory, token)
            monitor = watch.HookMonitor(directory, warnings.append)
            monitor.scan(final=True)
            self.assertEqual(warnings, [])
            self.assertEqual(len(monitor.completed), 1)
            for path in Path(directory).iterdir():
                self.assertEqual(path.read_bytes(), b'')

    def test_interrupted_process_is_reported_without_stopping_host(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            code = ('import importlib.util,os,signal,sys; '
                    's=importlib.util.spec_from_file_location("watch",sys.argv[1]); '
                    'm=importlib.util.module_from_spec(s);s.loader.exec_module(m); '
                    'm.mark_start(sys.argv[2]); os.kill(os.getpid(),signal.SIGKILL)')
            child = subprocess.run([sys.executable, '-c', code, str(WATCH), directory], timeout=5)
            self.assertNotEqual(child.returncode, 0)
            warnings = []
            monitor = watch.HookMonitor(directory, warnings.append)
            monitor.scan()
            monitor.scan()
            self.assertEqual(len(warnings), 1)
            self.assertIn('interrupted', warnings[0])
            self.assertIn('continue work', warnings[0])

    def test_hung_process_produces_bounded_status(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            process = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(5)'])
            try:
                (Path(directory) / ('start-' + str(process.pid) + '-' + 'a' * 32)).touch()
                timestamps = iter((0.0, 1.0))
                warnings = []
                monitor = watch.HookMonitor(directory, warnings.append, timeout_seconds=0.5,
                                            clock=lambda: next(timestamps))
                monitor.scan()
                monitor.scan()
                self.assertEqual(len(warnings), 1)
                self.assertIn('timed out', warnings[0])
                self.assertIsNone(process.poll())
            finally:
                process.kill()
                process.wait(timeout=5)

    def test_reported_warning_is_visible_once_even_after_hook_completion(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            token = watch.mark_start(directory)
            watch.mark_warning(directory, token)
            watch.mark_done(directory, token)
            warnings = []
            monitor = watch.HookMonitor(directory, warnings.append)
            monitor.scan()
            monitor.scan(final=True)
            self.assertEqual(len(warnings), 1)
            self.assertIn('hook reported a warning', warnings[0])
            self.assertEqual(len(monitor.completed), 1)

    def test_completion_between_directory_scan_and_liveness_check_is_not_failure(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('AGENT_CONTEXT_TEST_PARENT')) as directory:
            token = watch.mark_start(directory)
            warnings = []
            monitor = watch.HookMonitor(directory, warnings.append)
            def complete_before_exit(_pid):
                watch.mark_done(directory, token)
                return False
            with mock.patch.object(watch, 'process_alive', side_effect=complete_before_exit):
                monitor.scan()
            self.assertEqual(warnings, [])
            self.assertEqual(len(monitor.completed), 1)

    def test_missing_monitor_directory_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            warnings = []
            monitor = watch.HookMonitor(Path(directory) / 'missing', warnings.append)
            monitor.scan()
            self.assertEqual(len(warnings), 1)
            self.assertIn('unavailable', warnings[0])


if __name__ == '__main__':
    unittest.main()
